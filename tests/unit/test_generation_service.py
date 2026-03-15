"""Unit tests for generation orchestration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.application.exceptions import DatabaseOperationError
from app.application.models import CreateRecipeImageCommand
from app.application.services.generation_service import RecipeGenerationService
from app.application.services.image_prompt_builder import ImagePromptBuilder
from app.application.services.recipe_prompt_builder import RecipePromptBuilder
from app.config.settings import get_settings
from app.domain.enums import (
    GenerationJobStatus,
    GenerationJobType,
    GenerationSlotStatus,
    GenerationType,
)
from app.domain.time import get_current_utc_datetime
from app.infrastructure.database.repositories.generation_job_repository import (
    SqlAlchemyGenerationJobRepository,
)
from app.infrastructure.database.repositories.generation_schedule_slot_repository import (
    SqlAlchemyGenerationScheduleSlotRepository,
)
from app.infrastructure.database.repositories.recipe_repository import SqlAlchemyRecipeRepository
from tests.fakes.fake_components import (
    FakeDistributedLockManager,
    FakeObjectStorage,
    FakeRecipeImageGenerationProvider,
    FakeRecipeTextGenerationProvider,
)
from tests.integration.test_public_recipe_api import build_generated_recipe_payload


def build_generation_service(
    *,
    sqlite_session_factory,
    text_provider: FakeRecipeTextGenerationProvider,
    image_provider: FakeRecipeImageGenerationProvider,
    object_storage: FakeObjectStorage,
    recipe_repository_factory=SqlAlchemyRecipeRepository,
) -> RecipeGenerationService:
    """Create the generation service for tests."""

    settings = get_settings()
    return RecipeGenerationService(
        settings=settings,
        session_factory=sqlite_session_factory,
        recipe_repository_factory=lambda session: recipe_repository_factory(session=session),
        generation_job_repository_factory=lambda session: SqlAlchemyGenerationJobRepository(
            session=session
        ),
        generation_schedule_slot_repository_factory=lambda session: (
            SqlAlchemyGenerationScheduleSlotRepository(session=session)
        ),
        recipe_text_generation_provider=text_provider,
        recipe_image_generation_provider=image_provider,
        object_storage=object_storage,
        distributed_lock_manager=FakeDistributedLockManager(),
        recipe_prompt_builder=RecipePromptBuilder(),
        image_prompt_builder=ImagePromptBuilder(),
    )


def test_generation_service_is_idempotent_for_the_same_slot(sqlite_session_factory) -> None:
    """Running the same slot twice should not regenerate content."""

    text_provider = FakeRecipeTextGenerationProvider(payload=build_generated_recipe_payload())
    image_provider = FakeRecipeImageGenerationProvider()
    object_storage = FakeObjectStorage()
    generation_service = build_generation_service(
        sqlite_session_factory=sqlite_session_factory,
        text_provider=text_provider,
        image_provider=image_provider,
        object_storage=object_storage,
    )

    slot_time_utc = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
    first_result = generation_service.run_for_slot(
        slot_time_utc=slot_time_utc,
        requested_by="test-suite",
    )
    second_result = generation_service.run_for_slot(
        slot_time_utc=slot_time_utc,
        requested_by="test-suite",
    )

    assert first_result.was_created is True
    assert second_result.was_created is False
    assert text_provider.call_count == 1
    assert image_provider.call_count == 1
    assert first_result.recipe is not None
    assert second_result.recipe is not None
    assert second_result.recipe.id == first_result.recipe.id


def test_prepare_background_generation_does_not_reenqueue_pending_job(
    sqlite_session_factory,
) -> None:
    """Preparing the same slot twice should not claim a second enqueue while the job is pending."""

    text_provider = FakeRecipeTextGenerationProvider(payload=build_generated_recipe_payload())
    image_provider = FakeRecipeImageGenerationProvider()
    object_storage = FakeObjectStorage()
    generation_service = build_generation_service(
        sqlite_session_factory=sqlite_session_factory,
        text_provider=text_provider,
        image_provider=image_provider,
        object_storage=object_storage,
    )

    slot_time_utc = datetime(2026, 3, 15, 15, 0, tzinfo=UTC)
    first_dispatch_result = generation_service.prepare_background_generation(
        slot_time_utc=slot_time_utc,
        requested_by="test-suite",
    )
    second_dispatch_result = generation_service.prepare_background_generation(
        slot_time_utc=slot_time_utc,
        requested_by="test-suite",
    )

    assert first_dispatch_result.was_enqueued is True
    assert first_dispatch_result.job.status == GenerationJobStatus.PENDING
    assert second_dispatch_result.was_enqueued is False
    assert second_dispatch_result.job.status == GenerationJobStatus.PENDING
    assert second_dispatch_result.job.id == first_dispatch_result.job.id
    assert text_provider.call_count == 0
    assert image_provider.call_count == 0


class FailingRecipeRepository(SqlAlchemyRecipeRepository):
    """Repository that fails after recipe creation to test compensation."""

    def create_recipe_image(self, command: CreateRecipeImageCommand) -> None:
        _ = command
        raise DatabaseOperationError("Simulated database failure after upload.")


def test_generation_service_deletes_uploaded_image_on_database_failure(
    sqlite_session_factory,
) -> None:
    """A failed database write after upload should trigger storage cleanup."""

    text_provider = FakeRecipeTextGenerationProvider(payload=build_generated_recipe_payload())
    image_provider = FakeRecipeImageGenerationProvider()
    object_storage = FakeObjectStorage()
    generation_service = build_generation_service(
        sqlite_session_factory=sqlite_session_factory,
        text_provider=text_provider,
        image_provider=image_provider,
        object_storage=object_storage,
        recipe_repository_factory=FailingRecipeRepository,
    )

    slot_time_utc = datetime(2026, 3, 15, 13, 0, tzinfo=UTC)

    with pytest.raises(DatabaseOperationError):
        generation_service.run_for_slot(slot_time_utc=slot_time_utc, requested_by="test-suite")

    assert len(object_storage.deleted_keys) == 1


def test_generation_service_recovers_stale_running_job_before_retry(
    sqlite_session_factory,
) -> None:
    """A stale RUNNING job should be recovered and then regenerated."""

    settings = get_settings()
    text_provider = FakeRecipeTextGenerationProvider(payload=build_generated_recipe_payload())
    image_provider = FakeRecipeImageGenerationProvider()
    object_storage = FakeObjectStorage()
    generation_service = build_generation_service(
        sqlite_session_factory=sqlite_session_factory,
        text_provider=text_provider,
        image_provider=image_provider,
        object_storage=object_storage,
    )

    slot_time_utc = datetime(2026, 3, 15, 14, 0, tzinfo=UTC)
    stale_started_at = get_current_utc_datetime() - timedelta(
        seconds=settings.generation_stale_after_seconds + 60
    )

    with sqlite_session_factory() as session:
        slot_repository = SqlAlchemyGenerationScheduleSlotRepository(session=session)
        job_repository = SqlAlchemyGenerationJobRepository(session=session)

        schedule_slot = slot_repository.get_or_create_slot(
            slot_time_utc=slot_time_utc,
            generation_type=GenerationType.HOURLY_RECIPE,
        )
        schedule_slot = slot_repository.update_slot_status(
            slot_id=schedule_slot.id,
            status=GenerationSlotStatus.RUNNING,
            locked_at=stale_started_at,
        )
        job = job_repository.create_or_get_job(
            job_type=GenerationJobType.HOURLY_RECIPE_GENERATION,
            schedule_slot_id=schedule_slot.id,
            idempotency_key=f"hourly-recipe:{slot_time_utc.isoformat()}",
            provider_request_metadata={"requested_by": "stale-test"},
        )
        job_repository.update_job_status(
            job_id=job.id,
            status=GenerationJobStatus.RUNNING,
            started_at=stale_started_at,
            finished_at=None,
            error_message=None,
            retry_count=0,
            provider_request_metadata=job.provider_request_metadata,
            provider_response_metadata={},
        )
        session.commit()

    result = generation_service.run_for_slot(slot_time_utc=slot_time_utc, requested_by="test-suite")

    assert result.was_created is True
    assert result.job.status == GenerationJobStatus.COMPLETED
    assert result.job.retry_count == 1
    assert text_provider.call_count == 1
    assert image_provider.call_count == 1
