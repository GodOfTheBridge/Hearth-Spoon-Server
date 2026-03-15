"""Pydantic models used by the application and API boundaries."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    DifficultyLevel,
    GenerationJobStatus,
    GenerationJobType,
    GenerationSlotStatus,
    GenerationType,
    ModerationStatus,
    PublicationStatus,
)


class RecipeIngredient(BaseModel):
    """Structured ingredient item."""

    model_config = ConfigDict(extra="forbid")

    name: str
    amount: str
    unit: str
    notes: str


class RecipeStep(BaseModel):
    """Structured cooking step."""

    model_config = ConfigDict(extra="forbid")

    step_number: int
    title: str
    description: str
    duration_minutes: int
    temperature_celsius: int | None = None
    warnings: list[str] = Field(default_factory=list)


class RecipeGenerationParameters(BaseModel):
    """Parameters that define the generation style and constraints."""

    model_config = ConfigDict(extra="forbid")

    language_code: str
    cuisine_context: str
    dietary_context: str
    excluded_ingredients: list[str] = Field(default_factory=list)
    image_style: str
    maximum_ingredients: int
    maximum_steps: int


class GeneratedRecipePayload(BaseModel):
    """Validated provider payload before persistence."""

    model_config = ConfigDict(extra="forbid")

    title: str
    subtitle: str
    story_or_intro: str
    servings: int
    preparation_time_minutes: int
    cooking_time_minutes: int
    difficulty_level: DifficultyLevel
    ingredients: list[RecipeIngredient]
    tools: list[str]
    steps: list[RecipeStep]
    cooking_tips: list[str]
    plating_tips: list[str]
    style_tags: list[str]
    image_generation_brief: str


class GeneratedImageAsset(BaseModel):
    """Image bytes and metadata returned by the image provider."""

    model_config = ConfigDict(extra="forbid")

    content_bytes: bytes
    mime_type: str
    width: int | None = None
    height: int | None = None
    provider_name: str
    provider_model: str
    provider_response_metadata: dict[str, Any] = Field(default_factory=dict)


class StoredObject(BaseModel):
    """Object storage result after an upload succeeds."""

    model_config = ConfigDict(extra="forbid")

    storage_key: str
    public_url: str | None = None


class RecipeImage(BaseModel):
    """Persisted recipe image metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recipe_id: UUID
    storage_key: str
    public_url: str | None = None
    width: int | None = None
    height: int | None = None
    mime_type: str
    provider_name: str
    provider_model: str
    created_at: datetime


class Recipe(BaseModel):
    """Persisted recipe aggregate root."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    subtitle: str
    story_or_intro: str
    servings: int
    cooking_time_minutes: int
    preparation_time_minutes: int
    difficulty_level: DifficultyLevel
    ingredients: list[RecipeIngredient]
    tools: list[str]
    steps: list[RecipeStep]
    cooking_tips: list[str]
    plating_tips: list[str]
    style_tags: list[str]
    source_generation_parameters: RecipeGenerationParameters
    image_prompt: str
    moderation_status: ModerationStatus
    publication_status: PublicationStatus
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None


class RecipeAggregate(BaseModel):
    """Recipe with its primary image metadata."""

    model_config = ConfigDict(extra="forbid")

    recipe: Recipe
    image: RecipeImage | None = None


class GenerationScheduleSlot(BaseModel):
    """Persisted generation schedule slot."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slot_time_utc: datetime
    generation_type: GenerationType
    status: GenerationSlotStatus
    locked_at: datetime | None = None
    created_at: datetime


class GenerationJob(BaseModel):
    """Persisted generation job."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_type: GenerationJobType
    schedule_slot: datetime
    idempotency_key: str
    status: GenerationJobStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    retry_count: int
    provider_request_metadata: dict[str, Any] = Field(default_factory=dict)
    provider_response_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
