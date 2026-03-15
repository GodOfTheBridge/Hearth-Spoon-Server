"""Command and result models shared across application services."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities import (
    GeneratedRecipePayload,
    GenerationJob,
    GenerationScheduleSlot,
    Recipe,
    RecipeGenerationParameters,
)
from app.domain.enums import ModerationStatus, PublicationStatus


class CreateRecipeCommand(BaseModel):
    """Payload required to persist a newly generated recipe."""

    model_config = ConfigDict(extra="forbid")

    generated_recipe: GeneratedRecipePayload
    source_generation_parameters: RecipeGenerationParameters
    image_prompt: str
    moderation_status: ModerationStatus
    publication_status: PublicationStatus
    published_at: datetime | None = None


class CreateRecipeImageCommand(BaseModel):
    """Payload required to persist image metadata."""

    model_config = ConfigDict(extra="forbid")

    recipe_id: UUID
    storage_key: str
    public_url: str | None = None
    width: int | None = None
    height: int | None = None
    mime_type: str
    provider_name: str
    provider_model: str


class GenerationExecutionResult(BaseModel):
    """Result returned after a generation attempt."""

    model_config = ConfigDict(extra="forbid")

    job: GenerationJob
    schedule_slot: GenerationScheduleSlot
    recipe: Recipe | None = None
    was_created: bool
    message: str
    provider_metadata: dict[str, Any] = Field(default_factory=dict)
