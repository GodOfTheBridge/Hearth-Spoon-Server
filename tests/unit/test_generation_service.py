"""Unit tests for generation orchestration."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.application.exceptions import DatabaseOperationError
from app.application.models import CreateRecipeImageCommand
from app.application.services.generation_service import RecipeGenerationService
from app.application.services.image_prompt_builder import ImagePromptBuilder
from app.application.services.recipe_prompt_builder import RecipePromptBuilder
from app.config.settings import get_settings
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
