"""Object storage abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import StoredObject


class ObjectStorage(ABC):
    """Upload and access recipe images without leaking storage details upward."""

    @abstractmethod
    def upload_bytes(
        self,
        *,
        storage_key: str,
        content_bytes: bytes,
        content_type: str,
    ) -> StoredObject:
        """Upload an object and return its storage reference."""

    @abstractmethod
    def delete_object(self, *, storage_key: str) -> None:
        """Delete an object if it exists."""

    @abstractmethod
    def build_read_url(self, *, storage_key: str) -> str:
        """Build a public or signed URL for reading an object."""

    @abstractmethod
    def check_bucket_access(self) -> bool:
        """Return whether the target bucket is reachable."""
