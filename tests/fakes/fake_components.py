"""Reusable fake infrastructure for tests."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime

from app.application.ports.locking import DistributedLockManager
from app.application.ports.providers import RecipeImageGenerationProvider, RecipeTextGenerationProvider
from app.application.ports.storage import ObjectStorage
from app.domain.entities import GeneratedImageAsset, GeneratedRecipePayload, StoredObject


class FakeRecipeTextGenerationProvider(RecipeTextGenerationProvider):
    """Deterministic text provider for tests."""

    def __init__(self, *, payload: GeneratedRecipePayload) -> None:
        self.payload = payload
        self.call_count = 0

    def generate_recipe(
        self,
        *,
        slot_time_utc: datetime,
        parameters,
        system_prompt: str,
        user_prompt: str,
        safety_identifier: str,
    ):
        self.call_count += 1
        return (
            self.payload,
            {
                "slot_time_utc": slot_time_utc.isoformat(),
                "system_prompt_present": bool(system_prompt),
                "user_prompt_present": bool(user_prompt),
                "safety_identifier_hash": safety_identifier,
            },
            {"provider_response": "ok"},
        )


class FakeRecipeImageGenerationProvider(RecipeImageGenerationProvider):
    """Deterministic image provider for tests."""

    def __init__(self) -> None:
        self.call_count = 0

    def generate_image(self, *, prompt: str, safety_identifier: str):
        self.call_count += 1
        return (
            GeneratedImageAsset(
                content_bytes=b"fake-image",
                mime_type="image/png",
                width=1024,
                height=1024,
                provider_name="fake",
                provider_model="fake-image-model",
                provider_response_metadata={
                    "prompt": prompt,
                    "safety_identifier_hash": safety_identifier,
                },
            ),
            {"provider_response": "ok"},
        )


class FakeObjectStorage(ObjectStorage):
    """In-memory object storage for tests."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.deleted_keys: list[str] = []

    def upload_bytes(self, *, storage_key: str, content_bytes: bytes, content_type: str) -> StoredObject:
        self.objects[storage_key] = content_bytes
        return StoredObject(storage_key=storage_key, public_url=f"https://example.test/{storage_key}")

    def delete_object(self, *, storage_key: str) -> None:
        self.deleted_keys.append(storage_key)
        self.objects.pop(storage_key, None)

    def build_read_url(self, *, storage_key: str) -> str:
        return f"https://example.test/{storage_key}"

    def check_bucket_access(self) -> bool:
        return True


class FakeDistributedLockManager(DistributedLockManager):
    """Lock manager that can optionally refuse acquisition."""

    def __init__(self, *, should_acquire: bool = True) -> None:
        self.should_acquire = should_acquire

    @contextmanager
    def acquire_lock(
        self,
        *,
        lock_key: str,
        timeout_seconds: int,
        blocking_timeout_seconds: int,
    ):
        _ = (lock_key, timeout_seconds, blocking_timeout_seconds)
        if not self.should_acquire:
            yield None
            return
        yield object()
