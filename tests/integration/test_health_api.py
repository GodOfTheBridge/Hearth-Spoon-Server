"""Smoke test for the health endpoint."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.dependencies import get_health_service
from app.main import create_app
from tests.fakes.fake_components import NoopAdminRateLimiter


class FakeHealthService:
    """Simple fake health service."""

    def check_public_liveness(self) -> dict[str, object]:
        return {
            "status": "healthy",
            "timestamp_utc": datetime.now(UTC),
        }

    def check_readiness(self) -> dict[str, object]:
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
    assert "components" not in payload


def test_admin_readiness_endpoint_returns_detailed_payload() -> None:
    """The admin readiness endpoint should expose dependency detail to authenticated operators."""

    application = create_app()
    application.dependency_overrides[get_health_service] = lambda: FakeHealthService()

    with TestClient(application) as client:
        application.state.container.admin_rate_limiter = NoopAdminRateLimiter()
        response = client.get(
            "/api/v1/admin/health/readiness",
            headers={"Authorization": "Bearer test-read-token-which-is-long-enough"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["components"]["database"]["status"] == "healthy"
