"""SQLAlchemy persistence models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import (
    DifficultyLevel,
    GenerationJobStatus,
    GenerationJobType,
    GenerationSlotStatus,
    GenerationType,
    ModerationStatus,
    PublicationStatus,
)
from app.domain.time import get_current_utc_datetime
from app.infrastructure.database.base import Base
from app.infrastructure.database.types import JSON_VARIANT


def build_enum_column(enum_type: type[sa.Enum]) -> sa.Enum:
    """Create a string-backed enum column definition."""

    return sa.Enum(enum_type, native_enum=False, length=64)


class RecipeModel(Base):
    """Recipe persistence model."""

    __tablename__ = "recipes"

    id: Mapped[UUID] = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(sa.String(length=255))
    subtitle: Mapped[str] = mapped_column(sa.String(length=255))
    story_or_intro: Mapped[str] = mapped_column(sa.Text())
    servings: Mapped[int] = mapped_column(sa.Integer())
    cooking_time_minutes: Mapped[int] = mapped_column(sa.Integer())
    preparation_time_minutes: Mapped[int] = mapped_column(sa.Integer())
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(build_enum_column(DifficultyLevel))
    ingredients: Mapped[list[dict[str, object]]] = mapped_column(JSON_VARIANT)
    tools: Mapped[list[str]] = mapped_column(JSON_VARIANT)
    steps: Mapped[list[dict[str, object]]] = mapped_column(JSON_VARIANT)
    cooking_tips: Mapped[list[str]] = mapped_column(JSON_VARIANT)
    plating_tips: Mapped[list[str]] = mapped_column(JSON_VARIANT)
    style_tags: Mapped[list[str]] = mapped_column(JSON_VARIANT)
    source_generation_parameters: Mapped[dict[str, object]] = mapped_column(JSON_VARIANT)
    image_prompt: Mapped[str] = mapped_column(sa.Text())
    moderation_status: Mapped[ModerationStatus] = mapped_column(build_enum_column(ModerationStatus))
    publication_status: Mapped[PublicationStatus] = mapped_column(build_enum_column(PublicationStatus))
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=get_current_utc_datetime,
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=get_current_utc_datetime,
        onupdate=get_current_utc_datetime,
    )
    published_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    image: Mapped["RecipeImageModel | None"] = relationship(
        back_populates="recipe",
        uselist=False,
        cascade="all, delete-orphan",
    )


class RecipeImageModel(Base):
    """Recipe image persistence model."""

    __tablename__ = "recipe_images"
    __table_args__ = (UniqueConstraint("recipe_id", name="uq_recipe_images_recipe_id"),)

    id: Mapped[UUID] = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    recipe_id: Mapped[UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(sa.String(length=512))
    public_url: Mapped[str | None] = mapped_column(sa.String(length=1024), nullable=True)
    width: Mapped[int | None] = mapped_column(sa.Integer(), nullable=True)
    height: Mapped[int | None] = mapped_column(sa.Integer(), nullable=True)
    mime_type: Mapped[str] = mapped_column(sa.String(length=128))
    provider_name: Mapped[str] = mapped_column(sa.String(length=128))
    provider_model: Mapped[str] = mapped_column(sa.String(length=128))
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=get_current_utc_datetime,
    )

    recipe: Mapped[RecipeModel] = relationship(back_populates="image")


class GenerationScheduleSlotModel(Base):
    """Generation schedule slot persistence model."""

    __tablename__ = "generation_schedule_slots"
    __table_args__ = (
        UniqueConstraint("slot_time_utc", "generation_type", name="uq_generation_schedule_slot"),
    )

    id: Mapped[UUID] = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    slot_time_utc: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    generation_type: Mapped[GenerationType] = mapped_column(build_enum_column(GenerationType))
    status: Mapped[GenerationSlotStatus] = mapped_column(
        build_enum_column(GenerationSlotStatus),
        default=GenerationSlotStatus.PENDING,
    )
    locked_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=get_current_utc_datetime,
    )

    jobs: Mapped[list["GenerationJobModel"]] = relationship(back_populates="schedule_slot")


class GenerationJobModel(Base):
    """Generation job persistence model."""

    __tablename__ = "generation_jobs"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_generation_jobs_idempotency_key"),
    )

    id: Mapped[UUID] = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid4)
    job_type: Mapped[GenerationJobType] = mapped_column(build_enum_column(GenerationJobType))
    schedule_slot_id: Mapped[UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        ForeignKey("generation_schedule_slots.id", ondelete="CASCADE"),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(sa.String(length=255), nullable=False)
    status: Mapped[GenerationJobStatus] = mapped_column(
        build_enum_column(GenerationJobStatus),
        default=GenerationJobStatus.PENDING,
    )
    started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    retry_count: Mapped[int] = mapped_column(sa.Integer(), default=0)
    provider_request_metadata: Mapped[dict[str, object]] = mapped_column(
        JSON_VARIANT,
        default=dict,
    )
    provider_response_metadata: Mapped[dict[str, object]] = mapped_column(
        JSON_VARIANT,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=get_current_utc_datetime,
    )

    schedule_slot: Mapped[GenerationScheduleSlotModel] = relationship(back_populates="jobs")
