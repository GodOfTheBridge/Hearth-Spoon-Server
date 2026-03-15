"""Health checks for readiness-style diagnostics."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.application.ports.storage import ObjectStorage
from app.domain.time import get_current_utc_datetime


class HealthService:
    """Check database, Redis and object storage dependencies."""

    def __init__(
        self, *, database_engine: Engine, redis_client, object_storage: ObjectStorage
    ) -> None:
        self._database_engine = database_engine
        self._redis_client = redis_client
        self._object_storage = object_storage

    def check(self) -> dict[str, object]:
        """Return a structured health payload."""

        component_statuses: dict[str, dict[str, object]] = {}

        try:
            with self._database_engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            component_statuses["database"] = {"status": "healthy"}
        except Exception:  # noqa: BLE001
            component_statuses["database"] = {
                "status": "unhealthy",
                "detail": "database check failed",
            }

        try:
            redis_result = self._redis_client.ping()
            component_statuses["redis"] = {"status": "healthy" if redis_result else "unhealthy"}
        except Exception:  # noqa: BLE001
            component_statuses["redis"] = {
                "status": "unhealthy",
                "detail": "redis check failed",
            }

        try:
            storage_ok = self._object_storage.check_bucket_access()
            component_statuses["storage"] = {"status": "healthy" if storage_ok else "unhealthy"}
        except Exception:  # noqa: BLE001
            component_statuses["storage"] = {
                "status": "unhealthy",
                "detail": "storage check failed",
            }

        overall_status = "healthy"
        if any(component["status"] != "healthy" for component in component_statuses.values()):
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp_utc": get_current_utc_datetime(),
            "components": component_statuses,
        }
