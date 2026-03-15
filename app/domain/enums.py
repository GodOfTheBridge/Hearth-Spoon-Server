"""Stable enums used across the application."""

from __future__ import annotations

from enum import StrEnum


class DifficultyLevel(StrEnum):
    """Supported recipe difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ModerationStatus(StrEnum):
    """Moderation state for generated recipes."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PublicationStatus(StrEnum):
    """Publication state exposed to public clients."""

    DRAFT = "draft"
    PUBLISHED = "published"
    UNPUBLISHED = "unpublished"


class GenerationJobStatus(StrEnum):
    """Lifecycle states for a generation job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationSlotStatus(StrEnum):
    """Lifecycle states for a generation schedule slot."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationType(StrEnum):
    """Supported schedule slot generation types."""

    HOURLY_RECIPE = "hourly_recipe"


class GenerationJobType(StrEnum):
    """Supported generation jobs."""

    HOURLY_RECIPE_GENERATION = "hourly_recipe_generation"
