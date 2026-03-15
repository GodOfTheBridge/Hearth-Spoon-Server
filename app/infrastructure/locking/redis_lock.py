"""Redis-backed distributed lock implementation."""

from __future__ import annotations

from contextlib import contextmanager

import redis
from redis.exceptions import LockError

from app.application.ports.locking import DistributedLock, DistributedLockManager


class RedisDistributedLock(DistributedLock):
    """Thin wrapper around a Redis lock object."""

    def __init__(self, *, lock: redis.lock.Lock) -> None:
        self._lock = lock

    def __enter__(self) -> "RedisDistributedLock":
        """Enter the lock context."""

        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Release the lock context."""

        try:
            self._lock.release()
        except LockError:
            return None
        return None


class RedisDistributedLockManager(DistributedLockManager):
    """Acquire coarse-grained distributed locks in Redis."""

    def __init__(self, *, redis_client: redis.Redis) -> None:
        self._redis_client = redis_client

    @contextmanager
    def acquire_lock(
        self,
        *,
        lock_key: str,
        timeout_seconds: int,
        blocking_timeout_seconds: int,
    ):
        """Acquire a Redis lock or yield None if another worker already holds it."""

        redis_lock = self._redis_client.lock(
            name=lock_key,
            timeout=timeout_seconds,
            blocking_timeout=blocking_timeout_seconds,
        )
        acquired = redis_lock.acquire(blocking=True)
        if not acquired:
            yield None
            return

        distributed_lock = RedisDistributedLock(lock=redis_lock)
        try:
            yield distributed_lock
        finally:
            distributed_lock.__exit__(None, None, None)
