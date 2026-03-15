"""Distributed locking abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager


class DistributedLock(ABC):
    """Represents an acquired distributed lock."""

    @abstractmethod
    def __enter__(self) -> "DistributedLock":
        """Enter the lock context."""

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Release the lock context."""


class DistributedLockManager(ABC):
    """Acquire and release distributed locks."""

    @abstractmethod
    def acquire_lock(
        self,
        *,
        lock_key: str,
        timeout_seconds: int,
        blocking_timeout_seconds: int,
    ) -> AbstractContextManager[DistributedLock | None]:
        """Acquire a lock or return a context manager that yields None."""
