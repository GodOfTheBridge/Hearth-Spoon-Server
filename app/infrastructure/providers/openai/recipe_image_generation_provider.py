"""OpenAI implementation of the image generation provider."""

from __future__ import annotations

from app.application.ports.providers import RecipeImageGenerationProvider
from app.domain.constants import OPENAI_PROVIDER_NAME
from app.domain.entities import GeneratedImageAsset
from app.infrastructure.providers.openai.client import OpenAIClientWrapper


class OpenAIRecipeImageGenerationProvider(RecipeImageGenerationProvider):
    """Generate recipe images with the OpenAI Images API."""

    def __init__(self, *, openai_client_wrapper: OpenAIClientWrapper, model_name: str) -> None:
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
            provider_name=OPENAI_PROVIDER_NAME,
            provider_model=self._model_name,
            provider_response_metadata=response_metadata,
        )
        return image_asset, response_metadata
