"""Unit tests for OpenAI provider adapters."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.entities import RecipeGenerationParameters
from app.infrastructure.providers.openai.recipe_image_generation_provider import (
    OpenAIRecipeImageGenerationProvider,
)
from app.infrastructure.providers.openai.recipe_text_generation_provider import (
    OpenAIRecipeTextGenerationProvider,
)
from tests.integration.test_public_recipe_api import build_generated_recipe_payload


class FakeOpenAIClientWrapper:
    """Small fake for provider adapter tests."""

    def generate_structured_recipe(self, *, system_prompt, user_prompt, schema_definition, safety_identifier):
        _ = (system_prompt, user_prompt, schema_definition, safety_identifier)
        return build_generated_recipe_payload().model_dump(mode="json"), {"request": "ok"}, {"response": "ok"}

    def generate_image(self, *, prompt, safety_identifier):
        _ = (prompt, safety_identifier)
        return b"image", "image/png", {"response": "ok"}


def test_text_generation_provider_validates_payload() -> None:
    """The text generation provider should validate and normalize payloads."""

    provider = OpenAIRecipeTextGenerationProvider(openai_client_wrapper=FakeOpenAIClientWrapper())
    payload, request_metadata, response_metadata = provider.generate_recipe(
        slot_time_utc=datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc),
        parameters=RecipeGenerationParameters(
            language_code="ru-RU",
            cuisine_context="home cooking",
            dietary_context="balanced",
            excluded_ingredients=[],
            image_style="editorial food photography",
            maximum_ingredients=12,
            maximum_steps=8,
        ),
        system_prompt="system",
        user_prompt="user",
        safety_identifier="hash",
    )

    assert payload.title == "Сливочная паста с грибами"
    assert request_metadata["request"] == "ok"
    assert response_metadata["response"] == "ok"


def test_image_generation_provider_returns_normalized_asset() -> None:
    """The image provider should normalize raw client output."""

    provider = OpenAIRecipeImageGenerationProvider(
        openai_client_wrapper=FakeOpenAIClientWrapper(),
        model_name="gpt-image-1.5",
    )
    image_asset, response_metadata = provider.generate_image(prompt="dish", safety_identifier="hash")

    assert image_asset.content_bytes == b"image"
    assert image_asset.provider_model == "gpt-image-1.5"
    assert response_metadata["response"] == "ok"
