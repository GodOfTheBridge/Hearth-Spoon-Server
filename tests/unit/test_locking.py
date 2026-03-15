"""Unit tests for distributed locking adapters."""

from __future__ import annotations

from contextlib import contextmanager

from app.application.ports.locking import DistributedLock, DistributedLockManager
from app.infrastructure.locking.composite_lock import CompositeDistributedLockManager
from app.infrastructure.locking.postgres_lock import build_postgres_lock_id

SIGNED_INT64_MAX = 2**63 - 1
SIGNED_INT64_MIN = -(2**63)


class RecordingLock(DistributedLock):
    """Test lock that records when it has been released."""

    def __init__(self) -> None:
        self.was_released = False

    def __enter__(self) -> RecordingLock:
        """Enter the lock context."""

        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Mark the lock as released."""

        self.was_released = True


class RecordingLockManager(DistributedLockManager):
    """Lock manager that exposes acquired locks for assertions."""

    def __init__(self, *, should_acquire: bool = True) -> None:
        self.should_acquire = should_acquire
        self.acquired_locks: list[RecordingLock] = []

    @contextmanager
    def acquire_lock(
        self,
        *,
        lock_key: str,
        timeout_seconds: int,
        blocking_timeout_seconds: int,
    ):
        """Acquire a deterministic lock for tests."""

        _ = (lock_key, timeout_seconds, blocking_timeout_seconds)
        if not self.should_acquire:
            yield None
            return

        recording_lock = RecordingLock()
        self.acquired_locks.append(recording_lock)
        try:
            yield recording_lock
        finally:
            recording_lock.__exit__(None, None, None)


def test_build_postgres_lock_id_is_stable_signed_int64_value() -> None:
    """The advisory lock id should be deterministic and fit PostgreSQL bigint."""

    first_lock_id = build_postgres_lock_id("slot:2026-03-15T12")
    second_lock_id = build_postgres_lock_id("slot:2026-03-15T12")

    assert first_lock_id == second_lock_id
    assert SIGNED_INT64_MIN <= first_lock_id <= SIGNED_INT64_MAX


def test_composite_lock_manager_returns_last_acquired_lock() -> None:
    """The composite manager should expose the final acquired lock to callers."""

    first_lock_manager = RecordingLockManager()
    second_lock_manager = RecordingLockManager()
    composite_lock_manager = CompositeDistributedLockManager(
        lock_managers=[first_lock_manager, second_lock_manager]
    )

    with composite_lock_manager.acquire_lock(
        lock_key="generation-slot",
        timeout_seconds=30,
        blocking_timeout_seconds=1,
    ) as acquired_lock:
        assert acquired_lock is second_lock_manager.acquired_locks[0]
        assert first_lock_manager.acquired_locks[0].was_released is False
        assert second_lock_manager.acquired_locks[0].was_released is False

    assert first_lock_manager.acquired_locks[0].was_released is True
    assert second_lock_manager.acquired_locks[0].was_released is True


def test_composite_lock_manager_releases_previous_locks_when_later_lock_fails() -> None:
    """Already-acquired locks should be released if a later manager refuses acquisition."""

    first_lock_manager = RecordingLockManager()
    second_lock_manager = RecordingLockManager(should_acquire=False)
    composite_lock_manager = CompositeDistributedLockManager(
        lock_managers=[first_lock_manager, second_lock_manager]
    )

    with composite_lock_manager.acquire_lock(
        lock_key="generation-slot",
        timeout_seconds=30,
        blocking_timeout_seconds=1,
    ) as acquired_lock:
        assert acquired_lock is None
        assert first_lock_manager.acquired_locks[0].was_released is False

    assert first_lock_manager.acquired_locks[0].was_released is True
