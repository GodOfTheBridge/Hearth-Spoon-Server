"""Composite distributed lock manager for layered locking strategies."""

from __future__ import annotations

from contextlib import ExitStack, contextmanager

from app.application.ports.locking import DistributedLock, DistributedLockManager


class CompositeDistributedLockManager(DistributedLockManager):
    """Acquire multiple distributed locks as a single logical lock."""

    def __init__(self, *, lock_managers: list[DistributedLockManager]) -> None:
        self._lock_managers = lock_managers

    @contextmanager
    def acquire_lock(
        self,
        *,
        lock_key: str,
        timeout_seconds: int,
        blocking_timeout_seconds: int,
    ):
        """Acquire each configured lock manager in order."""

        with ExitStack() as exit_stack:
            acquired_locks: list[DistributedLock] = []
            for lock_manager in self._lock_managers:
                lock_context = lock_manager.acquire_lock(
                    lock_key=lock_key,
                    timeout_seconds=timeout_seconds,
                    blocking_timeout_seconds=blocking_timeout_seconds,
                )
                acquired_lock = exit_stack.enter_context(lock_context)
                if acquired_lock is None:
                    yield None
                    return
                acquired_locks.append(acquired_lock)

            yield acquired_locks[-1] if acquired_locks else None
