"""PostgreSQL advisory lock implementation."""

from __future__ import annotations

import time
from contextlib import contextmanager
from hashlib import sha256

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from app.application.ports.locking import DistributedLock, DistributedLockManager

POSTGRES_LOCK_POLL_INTERVAL_SECONDS = 0.1


def build_postgres_lock_id(lock_key: str) -> int:
    """Convert a lock key into a signed 64-bit advisory lock identifier."""

    digest = sha256(lock_key.encode()).digest()[:8]
    return int.from_bytes(digest, byteorder="big", signed=True)


class PostgresAdvisoryLock(DistributedLock):
    """Session-scoped PostgreSQL advisory lock."""

    def __init__(self, *, connection: Connection, lock_id: int) -> None:
        self._connection = connection
        self._lock_id = lock_id

    def __enter__(self) -> PostgresAdvisoryLock:
        """Enter the advisory lock context."""

        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Release the advisory lock and close the dedicated connection."""

        try:
            self._connection.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": self._lock_id},
            )
        finally:
            self._connection.close()


class PostgresAdvisoryLockManager(DistributedLockManager):
    """Acquire distributed locks backed by PostgreSQL advisory locks."""

    def __init__(self, *, database_engine: Engine) -> None:
        self._database_engine = database_engine

    @contextmanager
    def acquire_lock(
        self,
        *,
        lock_key: str,
        timeout_seconds: int,
        blocking_timeout_seconds: int,
    ):
        """Acquire an advisory lock or yield None if another session already holds it."""

        _ = timeout_seconds
        lock_id = build_postgres_lock_id(lock_key)
        deadline = time.monotonic() + blocking_timeout_seconds
        connection = self._database_engine.connect()

        try:
            while True:
                result = connection.execute(
                    text("SELECT pg_try_advisory_lock(:lock_id)"),
                    {"lock_id": lock_id},
                )
                was_acquired = bool(result.scalar())
                if was_acquired:
                    advisory_lock = PostgresAdvisoryLock(connection=connection, lock_id=lock_id)
                    try:
                        yield advisory_lock
                    finally:
                        advisory_lock.__exit__(None, None, None)
                    return

                if time.monotonic() >= deadline:
                    yield None
                    return

                time.sleep(POSTGRES_LOCK_POLL_INTERVAL_SECONDS)
        finally:
            if not connection.closed:
                connection.close()
