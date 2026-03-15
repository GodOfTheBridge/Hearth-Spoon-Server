"""Thin OpenAI SDK wrapper with retries, timeouts and metadata extraction."""

from __future__ import annotations

import base64
import json
from typing import Any

import structlog
from openai import APIConnectionError, APIStatusError, APITimeoutError, InternalServerError, OpenAI, RateLimitError
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config.settings import Settings
from app.domain.exceptions import ExternalProviderError

logger = structlog.get_logger(__name__)

TRANSIENT_OPENAI_EXCEPTIONS = (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)


class OpenAIClientWrapper:
    """Wrap the OpenAI SDK behind a focused, testable surface."""

    def __init__(self, *, settings: Settings) -> None:
        self._settings = settings
        self._client = OpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            project=settings.openai_project_id,
            max_retries=0,
        )

    def generate_structured_recipe(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_definition: dict[str, Any],
        safety_identifier: str,
    ) -> tuple[dict[str, Any], dict[str, object], dict[str, object]]:
        """Call the Responses API with strict JSON schema output."""

        request_metadata: dict[str, object] = {
            "provider": "openai",
            "operation": "responses.create",
            "model": self._settings.openai_text_model,
            "schema_name": schema_definition.get("name"),
        }
        logger.info("openai.responses.request.started", **request_metadata)

        try:
            for attempt in Retrying(
                stop=stop_after_attempt(self._settings.openai_max_retry_attempts),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type(TRANSIENT_OPENAI_EXCEPTIONS),
                reraise=True,
            ):
                with attempt:
                    response = self._client.responses.create(
                        model=self._settings.openai_text_model,
                        input=[
                            {
                                "role": "system",
                                "content": [{"type": "input_text", "text": system_prompt}],
                            },
                            {
                                "role": "user",
                                "content": [{"type": "input_text", "text": user_prompt}],
                            },
                        ],
                        text={"format": schema_definition},
                        max_output_tokens=self._settings.openai_max_output_tokens,
                        safety_identifier=safety_identifier,
                        timeout=self._settings.openai_text_timeout_seconds,
                    )
        except TRANSIENT_OPENAI_EXCEPTIONS as error:
            raise ExternalProviderError("OpenAI text generation temporarily failed.") from error
        except APIStatusError as error:
            raise ExternalProviderError(
                f"OpenAI text generation failed with status {error.status_code}."
            ) from error
        except Exception as error:  # noqa: BLE001
            raise ExternalProviderError("OpenAI text generation failed unexpectedly.") from error

        output_text = self._extract_output_text(response)
        try:
            raw_payload = json.loads(output_text)
        except json.JSONDecodeError as error:
            raise ExternalProviderError("OpenAI structured response was not valid JSON.") from error

        response_metadata = self._build_response_metadata(response)
        logger.info("openai.responses.request.completed", response_id=response_metadata.get("response_id"))
        return raw_payload, request_metadata, response_metadata

    def generate_image(
        self,
        *,
        prompt: str,
        safety_identifier: str,
    ) -> tuple[bytes, str, dict[str, object]]:
        """Call the Images API and return decoded bytes and response metadata."""

        logger.info(
            "openai.images.request.started",
            provider="openai",
            operation="images.generate",
            model=self._settings.openai_image_model,
        )

        try:
            for attempt in Retrying(
                stop=stop_after_attempt(self._settings.openai_max_retry_attempts),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type(TRANSIENT_OPENAI_EXCEPTIONS),
                reraise=True,
            ):
                with attempt:
                    response = self._client.images.generate(
                        model=self._settings.openai_image_model,
                        prompt=prompt,
                        size=self._settings.image_output_size,
                        quality=self._settings.image_output_quality,
                        output_format=self._settings.image_output_format,
                        timeout=self._settings.openai_image_timeout_seconds,
                    )
        except TRANSIENT_OPENAI_EXCEPTIONS as error:
            raise ExternalProviderError("OpenAI image generation temporarily failed.") from error
        except APIStatusError as error:
            raise ExternalProviderError(
                f"OpenAI image generation failed with status {error.status_code}."
            ) from error
        except Exception as error:  # noqa: BLE001
            raise ExternalProviderError("OpenAI image generation failed unexpectedly.") from error

        image_payload = response.data[0]
        encoded_image = getattr(image_payload, "b64_json", None)
        if not encoded_image:
            raise ExternalProviderError("OpenAI image generation did not return image bytes.")

        image_bytes = base64.b64decode(encoded_image)
        mime_type = f"image/{self._settings.image_output_format}"
        response_metadata = {
            "provider": "openai",
            "response_created": getattr(response, "created", None),
            "model": self._settings.openai_image_model,
            "revised_prompt": getattr(image_payload, "revised_prompt", None),
            "safety_identifier_hash": safety_identifier,
        }
        logger.info("openai.images.request.completed", model=self._settings.openai_image_model)
        return image_bytes, mime_type, response_metadata

    @staticmethod
    def _extract_output_text(response: Any) -> str:
        """Extract text content from the Responses API object."""

        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text:
            return output_text

        output_items = getattr(response, "output", [])
        for output_item in output_items:
            for content_item in getattr(output_item, "content", []):
                text_value = getattr(content_item, "text", None)
                if isinstance(text_value, str) and text_value:
                    return text_value
        raise ExternalProviderError("OpenAI response did not contain output text.")

    @staticmethod
    def _build_response_metadata(response: Any) -> dict[str, object]:
        """Extract a small, storage-safe metadata subset from the provider response."""

        usage = getattr(response, "usage", None)
        return {
            "response_id": getattr(response, "id", None),
            "model": getattr(response, "model", None),
            "status": getattr(response, "status", None),
            "usage": usage.model_dump() if usage and hasattr(usage, "model_dump") else None,
        }
