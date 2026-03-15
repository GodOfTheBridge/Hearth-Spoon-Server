"""Repository abstractions for database access."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.application.models import CreateRecipeCommand, CreateRecipeImageCommand
from app.domain.entities import GenerationJob, GenerationScheduleSlot, Recipe, RecipeAggregate
from app.domain.enums import GenerationJobStatus, GenerationJobType, GenerationSlotStatus, GenerationType


class RecipeRepository(ABC):
    """Persistence operations for recipes and recipe images."""

    @abstractmethod
    def get_latest_published(self) -> RecipeAggregate | None:
        """Return the latest published recipe aggregate."""

    @abstractmethod
    def list_published_feed(self, *, limit: int, offset: int) -> list[RecipeAggregate]:
        """Return a paginated public feed."""

    @abstractmethod
    def get_published_by_id(self, recipe_id: UUID) -> RecipeAggregate | None:
        """Return a published recipe aggregate by identifier."""

    @abstractmethod
    def get_by_id(self, recipe_id: UUID) -> RecipeAggregate | None:
        """Return any recipe aggregate by identifier, regardless of publication state."""

    @abstractmethod
    def create_recipe(self, command: CreateRecipeCommand) -> Recipe:
        """Persist a generated recipe."""

    @abstractmethod
    def create_recipe_image(self, command: CreateRecipeImageCommand) -> None:
        """Persist image metadata for a recipe."""

    @abstractmethod
    def publish_recipe(self, recipe_id: UUID, published_at: datetime) -> Recipe:
        """Publish a recipe."""

    @abstractmethod
    def unpublish_recipe(self, recipe_id: UUID) -> Recipe:
        """Unpublish a recipe."""


class GenerationScheduleSlotRepository(ABC):
    """Persistence operations for schedule slots."""

    @abstractmethod
    def get_by_id(self, slot_id: UUID) -> GenerationScheduleSlot | None:
        """Return a slot by identifier."""

    @abstractmethod
    def get_or_create_slot(
        self,
        *,
        slot_time_utc: datetime,
        generation_type: GenerationType,
    ) -> GenerationScheduleSlot:
        """Return an existing slot or create a new one."""

    @abstractmethod
    def update_slot_status(
        self,
        *,
        slot_id: UUID,
        status: GenerationSlotStatus,
        locked_at: datetime | None = None,
    ) -> GenerationScheduleSlot:
        """Update the slot status."""


class GenerationJobRepository(ABC):
    """Persistence operations for generation jobs."""

    @abstractmethod
    def get_by_id(self, job_id: UUID) -> GenerationJob | None:
        """Return a job by identifier."""

    @abstractmethod
    def get_by_idempotency_key(self, idempotency_key: str) -> GenerationJob | None:
        """Return a job by idempotency key."""

    @abstractmethod
    def get_latest_by_slot(self, slot_id: UUID) -> GenerationJob | None:
        """Return the latest job associated with a slot."""

    @abstractmethod
    def create_or_get_job(
        self,
        *,
        job_type: GenerationJobType,
        schedule_slot_id: UUID,
        idempotency_key: str,
        provider_request_metadata: dict[str, object],
    ) -> GenerationJob:
        """Create a job or return the existing row for the same idempotency key."""

    @abstractmethod
    def update_job_status(
        self,
        *,
        job_id: UUID,
        status: GenerationJobStatus,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        error_message: str | None = None,
        retry_count: int | None = None,
        provider_request_metadata: dict[str, object] | None = None,
        provider_response_metadata: dict[str, object] | None = None,
    ) -> GenerationJob:
        """Update job state and metadata."""
