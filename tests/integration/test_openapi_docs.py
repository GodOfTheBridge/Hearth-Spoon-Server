"""Integration tests for developer-facing OpenAPI docs."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config.settings import get_settings
from app.main import create_app


def test_docs_and_redoc_are_available_in_development(monkeypatch) -> None:
    """Swagger UI, ReDoc, and raw OpenAPI should be served for development usage."""

    monkeypatch.setenv("APP_ENVIRONMENT", "development")
    get_settings.cache_clear()
    application = create_app()

    with TestClient(application) as client:
        docs_response = client.get("/docs")
        redoc_response = client.get("/redoc")
        openapi_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert "Swagger UI" in docs_response.text
    assert redoc_response.status_code == 200
    assert "ReDoc" in redoc_response.text
    assert openapi_response.status_code == 200


def test_openapi_metadata_security_and_examples_are_exposed(monkeypatch) -> None:
    """OpenAPI metadata should expose the configured tags, auth scheme, and examples."""

    monkeypatch.setenv("APP_ENVIRONMENT", "development")
    get_settings.cache_clear()
    application = create_app()

    with TestClient(application) as client:
        payload = client.get("/openapi.json").json()

    assert payload["info"]["title"] == "ПечьДаЛожка Backend"
    assert payload["info"]["version"] == "0.1.0"
    assert payload["info"]["description"].startswith("Trusted backend API")
    assert [tag["name"] for tag in payload["tags"]] == ["public", "admin", "generation", "health"]
    assert payload["components"]["securitySchemes"]["AdminBearerAuth"]["scheme"] == "bearer"
    assert payload["paths"]["/api/v1/admin/generations/run-now"]["post"]["security"] == [
        {"AdminBearerAuth": []}
    ]
    assert (
        payload["components"]["schemas"]["RunGenerationNowRequest"]["example"]["slot_time_utc"]
        == "2026-03-15T12:00:00+00:00"
    )
    assert (
        payload["components"]["schemas"]["PublicRecipeDetailResponse"]["example"]["title"]
        == "Сливочная паста с грибами"
    )
