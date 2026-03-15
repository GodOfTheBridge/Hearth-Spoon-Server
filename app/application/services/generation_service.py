"""Main orchestration service for hourly recipe generation."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.orm import Session, sessionmaker

from app.application.exceptions import (
    DatabaseOperationError,
    IdempotencyConflictError,
    RetryExhaustedError,
)
from app.application.models import (
    CreateRecipeCommand,
    CreateRecipeImageCommand,
    GenerationExecutionResult,
)
from app.application.ports.locking import DistributedLockManager
from app.application.ports.providers import (
    RecipeImageGenerationProvider,
    RecipeTextGenerationProvider,
)
from app.application.ports.repositories import (
    GenerationJobRepository,
    GenerationScheduleSlotRepository,
    RecipeRepository,
)
from app.application.ports.storage import ObjectStorage
from app.application.services.image_prompt_builder import ImagePromptBuilder
from app.application.services.recipe_prompt_builder import RecipePromptBuilder
from app.config.settings import Settings
from app.domain.constants import GENERATION_LOCK_KEY_PREFIX, RECIPE_IMAGE_STORAGE_PREFIX
from app.domain.entities import Recipe, RecipeGenerationParameters
from app.domain.enums import (
    GenerationJobStatus,
    GenerationJobType,
    GenerationSlotStatus,
    GenerationType,
    ModerationStatus,
    PublicationStatus,
)
from app.domain.exceptions import StorageOperationError
from app.domain.time import get_current_utc_datetime, normalize_to_hour_slot
from app.observability.context import bind_context
from app.security.safety import build_hashed_safety_identifier

logger = structlog.get_logger(__name__)

RecipeRepositoryFactory = Callable[[Session], RecipeRepository]
GenerationJobRepositoryFactory = Callable[[Session], GenerationJobRepository]
GenerationScheduleSlotRepositoryFactory = Callable[[Session], GenerationScheduleSlotRepository]


class RecipeGenerationService:
    """Coordinate generation, persistence and failure handling."""

    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: sessionmaker[Session],
        recipe_repository_factory: RecipeRepositoryFactory,
        generation_job_repository_factory: GenerationJobRepositoryFactory,
        generation_schedule_slot_repository_factory: GenerationScheduleSlotRepositoryFactory,
        recipe_text_generation_provider: RecipeTextGenerationProvider,
        recipe_image_generation_provider: RecipeImageGenerationProvider,
        object_storage: ObjectStorage,
        distributed_lock_manager: DistributedLockManager,
        recipe_prompt_builder: RecipePromptBuilder,
        image_prompt_builder: ImagePromptBuilder,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._recipe_repository_factory = recipe_repository_factory
        self._generation_job_repository_factory = generation_job_repository_factory
        self._generation_schedule_slot_repository_factory = (
            generation_schedule_slot_repository_factory
        )
        self._recipe_text_generation_provider = recipe_text_generation_provider
        self._recipe_image_generation_provider = recipe_image_generation_provider
        self._object_storage = object_storage
        self._distributed_lock_manager = distributed_lock_manager
        self._recipe_prompt_builder = recipe_prompt_builder
        self._image_prompt_builder = image_prompt_builder

    def run_hourly_generation(
        self,
        *,
        requested_by: str,
        now_utc: datetime | None = None,
    ) -> GenerationExecutionResult:
        """Generate the recipe for the current UTC hour slot."""

        target_datetime = now_utc or get_current_utc_datetime()
        return self.run_for_slot(
            slot_time_utc=normalize_to_hour_slot(target_datetime),
            requested_by=requested_by,
        )

    def run_for_slot(
        self,
        *,
        slot_time_utc: datetime,
        requested_by: str,
    ) -> GenerationExecutionResult:
        """Generate a recipe for a specific UTC hour slot."""

        normalized_slot_time_utc = normalize_to_hour_slot(slot_time_utc)
        idempotency_key = f"hourly-recipe:{normalized_slot_time_utc.isoformat()}"
        lock_key = f"{GENERATION_LOCK_KEY_PREFIX}:{idempotency_key}"

        with self._distributed_lock_manager.acquire_lock(
            lock_key=lock_key,
            timeout_seconds=self._settings.generation_lock_timeout_seconds,
            blocking_timeout_seconds=0,
        ) as acquired_lock:
            if acquired_lock is None:
                raise IdempotencyConflictError(
                    "Generation for slot "
                    f"{normalized_slot_time_utc.isoformat()} is already running."
                )
            return self._execute_generation(
                normalized_slot_time_utc=normalized_slot_time_utc,
                requested_by=requested_by,
                idempotency_key=idempotency_key,
            )

    def _execute_generation(
        self,
        *,
        normalized_slot_time_utc: datetime,
        requested_by: str,
        idempotency_key: str,
    ) -> GenerationExecutionResult:
        now_utc = get_current_utc_datetime()
        generation_parameters = self._build_generation_parameters()
        request_metadata: dict[str, object] = {
            "requested_by": requested_by,
            "slot_time_utc": normalized_slot_time_utc.isoformat(),
            "generation_parameters": generation_parameters.model_dump(mode="json"),
        }

        schedule_slot, job = self._prepare_job(
            slot_time_utc=normalized_slot_time_utc,
            idempotency_key=idempotency_key,
            request_metadata=request_metadata,
        )
        bind_context(job_id=str(job.id))

        if job.status == GenerationJobStatus.COMPLETED:
            recipe = self._load_recipe_from_job(job.provider_response_metadata)
            return GenerationExecutionResult(
                job=job,
                schedule_slot=schedule_slot,
                recipe=recipe,
                was_created=False,
                message="The slot was already generated earlier.",
                provider_metadata=job.provider_response_metadata,
            )

        safety_identifier = build_hashed_safety_identifier(
            namespace="recipe-generation",
            raw_identifier=idempotency_key,
        )
        text_request_metadata: dict[str, object] = {}
        text_response_metadata: dict[str, object] = {}
        image_response_metadata: dict[str, object] = {}
        storage_key: str | None = None

        try:
            system_prompt = self._recipe_prompt_builder.build_system_prompt()
            user_prompt = self._recipe_prompt_builder.build_user_prompt(
                slot_time_utc=normalized_slot_time_utc,
                parameters=generation_parameters,
            )
            generated_recipe, text_request_metadata, text_response_metadata = (
                self._recipe_text_generation_provider.generate_recipe(
                    slot_time_utc=normalized_slot_time_utc,
                    parameters=generation_parameters,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    safety_identifier=safety_identifier,
                )
            )

            image_prompt = self._image_prompt_builder.build(
                generated_recipe=generated_recipe,
                generation_parameters=generation_parameters,
            )
            generated_image, image_response_metadata = (
                self._recipe_image_generation_provider.generate_image(
                    prompt=image_prompt,
                    safety_identifier=safety_identifier,
                )
            )

            storage_key = self._build_storage_key(slot_time_utc=normalized_slot_time_utc)
            stored_object = self._object_storage.upload_bytes(
                storage_key=storage_key,
                content_bytes=generated_image.content_bytes,
                content_type=generated_image.mime_type,
            )

            publication_status = (
                PublicationStatus.PUBLISHED
                if self._settings.auto_publish_generated_recipes
                else PublicationStatus.DRAFT
            )
            published_at = now_utc if publication_status == PublicationStatus.PUBLISHED else None

            create_recipe_command = CreateRecipeCommand(
                generated_recipe=generated_recipe,
                source_generation_parameters=generation_parameters,
                image_prompt=image_prompt,
                moderation_status=ModerationStatus.PENDING,
                publication_status=publication_status,
                published_at=published_at,
            )

            create_recipe_image_command = CreateRecipeImageCommand(
                recipe_id=UUID(int=0),
                storage_key=stored_object.storage_key,
                public_url=stored_object.public_url,
                width=generated_image.width,
                height=generated_image.height,
                mime_type=generated_image.mime_type,
                provider_name=generated_image.provider_name,
                provider_model=generated_image.provider_model,
            )

            recipe = self._persist_success(
                schedule_slot_id=schedule_slot.id,
                job_id=job.id,
                create_recipe_command=create_recipe_command,
                create_recipe_image_command=create_recipe_image_command,
                text_request_metadata=text_request_metadata,
                text_response_metadata=text_response_metadata,
                image_response_metadata=image_response_metadata,
                storage_key=stored_object.storage_key,
            )

            return GenerationExecutionResult(
                job=self._load_job(job.id),
                schedule_slot=self._load_slot(schedule_slot.id),
                recipe=recipe,
                was_created=True,
                message="Recipe and image were generated successfully.",
                provider_metadata={
                    "text_generation": text_response_metadata,
                    "image_generation": image_response_metadata,
                    "storage": {"storage_key": stored_object.storage_key},
                },
            )
        except Exception as error:  # noqa: BLE001
            failure_metadata: dict[str, object] = {
                "text_generation": text_response_metadata,
                "image_generation": image_response_metadata,
                "storage_key": storage_key,
            }
            try:
                self._handle_failure(
                    job_id=job.id,
                    schedule_slot_id=schedule_slot.id,
                    existing_retry_count=job.retry_count,
                    storage_key=storage_key,
                    failure_metadata=failure_metadata,
                    error=error,
                )
            except Exception:  # noqa: BLE001
                logger.exception(
                    "generation.job.failure_handler_failed",
                    job_id=str(job.id),
                    schedule_slot_id=str(schedule_slot.id),
                    original_error_type=type(error).__name__,
                )
            raise

    def _prepare_job(
        self,
        *,
        slot_time_utc: datetime,
        idempotency_key: str,
        request_metadata: dict[str, object],
    ):
        with self._session_factory() as session:
            slot_repository = self._generation_schedule_slot_repository_factory(session)
            schedule_slot = slot_repository.get_or_create_slot(
                slot_time_utc=slot_time_utc,
                generation_type=GenerationType.HOURLY_RECIPE,
            )
            session.commit()

        with self._session_factory() as session:
            slot_repository = self._generation_schedule_slot_repository_factory(session)
            job_repository = self._generation_job_repository_factory(session)

            persisted_schedule_slot = slot_repository.get_by_id(schedule_slot.id)
            if persisted_schedule_slot is None:
                raise DatabaseOperationError(
                    f"Generation schedule slot '{schedule_slot.id}' was not found after creation."
                )

            job = job_repository.create_or_get_job(
                job_type=GenerationJobType.HOURLY_RECIPE_GENERATION,
                schedule_slot_id=persisted_schedule_slot.id,
                idempotency_key=idempotency_key,
                provider_request_metadata=request_metadata,
            )

            if job.status == GenerationJobStatus.RUNNING:
                raise IdempotencyConflictError(
                    f"Generation job '{job.id}' is already running for this slot."
                )
            if job.status == GenerationJobStatus.FAILED and (
                job.retry_count >= self._settings.generation_max_retry_count
            ):
                raise RetryExhaustedError(
                    f"Generation retries are exhausted for slot {slot_time_utc.isoformat()}."
                )
            if job.status != GenerationJobStatus.COMPLETED:
                persisted_schedule_slot = slot_repository.update_slot_status(
                    slot_id=persisted_schedule_slot.id,
                    status=GenerationSlotStatus.RUNNING,
                    locked_at=get_current_utc_datetime(),
                )
                job = job_repository.update_job_status(
                    job_id=job.id,
                    status=GenerationJobStatus.RUNNING,
                    started_at=get_current_utc_datetime(),
                    finished_at=None,
                    error_message=None,
                    retry_count=job.retry_count,
                    provider_request_metadata=request_metadata,
                    provider_response_metadata=job.provider_response_metadata,
                )
                session.commit()

            return persisted_schedule_slot, job

    def _persist_success(
        self,
        *,
        schedule_slot_id: UUID,
        job_id: UUID,
        create_recipe_command: CreateRecipeCommand,
        create_recipe_image_command: CreateRecipeImageCommand,
        text_request_metadata: dict[str, object],
        text_response_metadata: dict[str, object],
        image_response_metadata: dict[str, object],
        storage_key: str,
    ) -> Recipe:
        with self._session_factory() as session:
            try:
                recipe_repository = self._recipe_repository_factory(session)
                slot_repository = self._generation_schedule_slot_repository_factory(session)
                job_repository = self._generation_job_repository_factory(session)

                recipe = recipe_repository.create_recipe(create_recipe_command)
                create_recipe_image_command.recipe_id = recipe.id
                recipe_repository.create_recipe_image(create_recipe_image_command)

                slot_repository.update_slot_status(
                    slot_id=schedule_slot_id,
                    status=GenerationSlotStatus.COMPLETED,
                    locked_at=get_current_utc_datetime(),
                )

                existing_job = job_repository.get_by_id(job_id)
                if existing_job is None:
                    raise DatabaseOperationError(
                        f"Generation job '{job_id}' disappeared unexpectedly."
                    )

                provider_request_metadata = dict(existing_job.provider_request_metadata)
                provider_request_metadata["text_generation"] = text_request_metadata
                provider_request_metadata["image_prompt"] = create_recipe_command.image_prompt

                provider_response_metadata: dict[str, object] = {
                    "recipe_id": str(recipe.id),
                    "text_generation": text_response_metadata,
                    "image_generation": image_response_metadata,
                    "storage": {"storage_key": storage_key},
                }

                job_repository.update_job_status(
                    job_id=job_id,
                    status=GenerationJobStatus.COMPLETED,
                    started_at=existing_job.started_at,
                    finished_at=get_current_utc_datetime(),
                    error_message=None,
                    retry_count=existing_job.retry_count,
                    provider_request_metadata=provider_request_metadata,
                    provider_response_metadata=provider_response_metadata,
                )
                session.commit()
                return recipe
            except Exception as error:  # noqa: BLE001
                session.rollback()
                raise DatabaseOperationError("Failed to persist the generated recipe.") from error

    def _handle_failure(
        self,
        *,
        job_id: UUID,
        schedule_slot_id: UUID,
        existing_retry_count: int,
        storage_key: str | None,
        failure_metadata: dict[str, object],
        error: Exception,
    ) -> None:
        if storage_key is not None:
            try:
                self._object_storage.delete_object(storage_key=storage_key)
                failure_metadata["storage_cleanup"] = "deleted_orphaned_object"
            except StorageOperationError:
                failure_metadata["storage_cleanup"] = "delete_failed"

        with self._session_factory() as session:
            try:
                slot_repository = self._generation_schedule_slot_repository_factory(session)
                job_repository = self._generation_job_repository_factory(session)
                existing_job = job_repository.get_by_id(job_id)
                if existing_job is None:
                    raise DatabaseOperationError(
                        f"Generation job '{job_id}' disappeared unexpectedly."
                    )

                slot_repository.update_slot_status(
                    slot_id=schedule_slot_id,
                    status=GenerationSlotStatus.FAILED,
                    locked_at=get_current_utc_datetime(),
                )
                job_repository.update_job_status(
                    job_id=job_id,
                    status=GenerationJobStatus.FAILED,
                    started_at=existing_job.started_at,
                    finished_at=get_current_utc_datetime(),
                    error_message=str(error),
                    retry_count=existing_retry_count + 1,
                    provider_request_metadata=existing_job.provider_request_metadata,
                    provider_response_metadata=failure_metadata,
                )
                session.commit()
            except Exception:
                session.rollback()
                raise

        logger.exception(
            "generation.job.failed",
            job_id=str(job_id),
            schedule_slot_id=str(schedule_slot_id),
            error_type=type(error).__name__,
        )

    def _load_job(self, job_id: UUID):
        with self._session_factory() as session:
            job_repository = self._generation_job_repository_factory(session)
            job = job_repository.get_by_id(job_id)
            if job is None:
                raise DatabaseOperationError(
                    f"Generation job '{job_id}' was not found after completion."
                )
            return job

    def _load_slot(self, schedule_slot_id: UUID):
        with self._session_factory() as session:
            slot_repository = self._generation_schedule_slot_repository_factory(session)
            slot = slot_repository.get_by_id(schedule_slot_id)
            if slot is None:
                raise DatabaseOperationError(
                    f"Generation schedule slot '{schedule_slot_id}' was not found after completion."
                )
            return slot

    def _load_recipe_from_job(self, provider_response_metadata: dict[str, object]) -> Recipe | None:
        recipe_id = provider_response_metadata.get("recipe_id")
        if not isinstance(recipe_id, str):
            return None
        with self._session_factory() as session:
            recipe_repository = self._recipe_repository_factory(session)
            recipe_aggregate = recipe_repository.get_by_id(UUID(recipe_id))
            return recipe_aggregate.recipe if recipe_aggregate else None

    def _build_generation_parameters(self) -> RecipeGenerationParameters:
        return RecipeGenerationParameters(
            language_code=self._settings.default_recipe_language_code,
            cuisine_context=self._settings.default_cuisine_context,
            dietary_context=self._settings.default_dietary_context,
            excluded_ingredients=self._settings.default_excluded_ingredients,
            image_style=self._settings.default_image_style,
            maximum_ingredients=self._settings.default_maximum_ingredients,
            maximum_steps=self._settings.default_maximum_steps,
        )

    def _build_storage_key(self, *, slot_time_utc: datetime) -> str:
        slot_date_path = slot_time_utc.strftime("%Y/%m/%d/%H")
        return f"{RECIPE_IMAGE_STORAGE_PREFIX}/{slot_date_path}/{uuid4()}.png"
