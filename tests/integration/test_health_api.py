"""Smoke test for the health endpoint."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.dependencies import get_health_service
from app.main import create_app


class FakeHealthService:
    """Simple fake health service."""

    def check(self) -> dict[str, object]:
        return {
            "status": "healthy",
            "timestamp_utc": datetime.now(UTC),
            "components": {
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
                "storage": {"status": "healthy"},
            },
        }


def test_health_endpoint_returns_healthy_payload() -> None:
    """The health endpoint should return HTTP 200 and a structured body."""

    application = create_app()
    application.dependency_overrides[get_health_service] = lambda: FakeHealthService()

    with TestClient(application) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["components"]["database"]["status"] == "healthy"
