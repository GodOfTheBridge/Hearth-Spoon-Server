"""OpenAI implementation of the image generation provider."""

from __future__ import annotations

from typing import Protocol

from app.application.ports.providers import RecipeImageGenerationProvider
from app.domain.constants import OPENAI_PROVIDER_NAME
from app.domain.entities import GeneratedImageAsset


class ImageGenerationClient(Protocol):
    """Protocol for the subset of client functionality needed by this provider."""

    def generate_image(
        self,
        *,
        prompt: str,
        safety_identifier: str,
    ) -> tuple[bytes, str, dict[str, object]]:
        """Generate an image."""


class OpenAIRecipeImageGenerationProvider(RecipeImageGenerationProvider):
    """Generate recipe images with the OpenAI Images API."""

    def __init__(self, *, openai_client_wrapper: ImageGenerationClient, model_name: str) -> None:
        self._openai_client_wrapper = openai_client_wrapper
        self._model_name = model_name

    def generate_image(
        self,
        *,
        prompt: str,
        safety_identifier: str,
    ) -> tuple[GeneratedImageAsset, dict[str, object]]:
        """Generate an image and return a normalized asset model."""

        image_bytes, mime_type, response_metadata = self._openai_client_wrapper.generate_image(
            prompt=prompt,
            safety_identifier=safety_identifier,
        )
        image_asset = GeneratedImageAsset(
            content_bytes=image_bytes,
            mime_type=mime_type,
            width=response_metadata.get("width")
            if isinstance(response_metadata.get("width"), int)
            else None,
            height=response_metadata.get("height")
            if isinstance(response_metadata.get("height"), int)
            else None,
            provider_name=OPENAI_PROVIDER_NAME,
            provider_model=self._model_name,
            provider_response_metadata=response_metadata,
        )
        return image_asset, response_metadata
