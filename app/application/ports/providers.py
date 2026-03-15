"""Provider abstractions used by the application layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.entities import GeneratedImageAsset, GeneratedRecipePayload, RecipeGenerationParameters


class RecipeTextGenerationProvider(ABC):
    """Generate a structured recipe payload."""

    @abstractmethod
    def generate_recipe(
        self,
        *,
        slot_time_utc: datetime,
        parameters: RecipeGenerationParameters,
        system_prompt: str,
        user_prompt: str,
        safety_identifier: str,
    ) -> tuple[GeneratedRecipePayload, dict[str, object], dict[str, object]]:
        """Generate a recipe and return payload, request metadata and response metadata."""


class RecipeImageGenerationProvider(ABC):
    """Generate a food image from a prompt."""

    @abstractmethod
    def generate_image(
        self,
        *,
        prompt: str,
        safety_identifier: str,
    ) -> tuple[GeneratedImageAsset, dict[str, object]]:
        """Generate an image and return the image asset and provider response metadata."""
