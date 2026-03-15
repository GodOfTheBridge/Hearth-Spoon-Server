"""OpenAI implementation of the recipe text generation provider."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.application.ports.providers import RecipeTextGenerationProvider
from app.domain.entities import GeneratedRecipePayload, RecipeGenerationParameters
from app.domain.recipe_schema import RECIPE_RESPONSE_JSON_SCHEMA, validate_recipe_payload


class StructuredRecipeClient(Protocol):
    """Protocol for the subset of client functionality needed by this provider."""

    def generate_structured_recipe(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_definition: dict[str, object],
        safety_identifier: str,
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        """Generate a structured recipe response."""


class OpenAIRecipeTextGenerationProvider(RecipeTextGenerationProvider):
    """Generate structured recipe JSON with the OpenAI Responses API."""

    def __init__(self, *, openai_client_wrapper: StructuredRecipeClient) -> None:
        self._openai_client_wrapper = openai_client_wrapper

    def generate_recipe(
        self,
        *,
        slot_time_utc: datetime,
        parameters: RecipeGenerationParameters,
        system_prompt: str,
        user_prompt: str,
        safety_identifier: str,
    ) -> tuple[GeneratedRecipePayload, dict[str, object], dict[str, object]]:
        """Generate and validate a recipe payload."""

        raw_payload, request_metadata, response_metadata = (
            self._openai_client_wrapper.generate_structured_recipe(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema_definition=RECIPE_RESPONSE_JSON_SCHEMA,
                safety_identifier=safety_identifier,
            )
        )
        validated_payload = validate_recipe_payload(raw_payload)
        request_metadata["slot_time_utc"] = slot_time_utc.isoformat()
        request_metadata["generation_parameters"] = parameters.model_dump(mode="json")
        return validated_payload, request_metadata, response_metadata
