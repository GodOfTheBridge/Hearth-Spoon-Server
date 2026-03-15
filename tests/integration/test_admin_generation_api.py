"""Integration tests for admin generation endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from app.config.settings import get_settings
from app.infrastructure.database.base import Base
from app.infrastructure.database.repositories.generation_job_repository import (
    SqlAlchemyGenerationJobRepository,
)
from app.infrastructure.database.repositories.recipe_repository import SqlAlchemyRecipeRepository
from app.main import create_app
from tests.fakes.fake_components import (
    FakeDistributedLockManager,
    FakeObjectStorage,
    FakeRecipeImageGenerationProvider,
    FakeRecipeTextGenerationProvider,
    NoopAdminRateLimiter,
)
from tests.integration.test_public_recipe_api import build_generated_recipe_payload


def configure_test_container(
    application,
) -> tuple[
    FakeRecipeTextGenerationProvider,
    FakeRecipeImageGenerationProvider,
    FakeObjectStorage,
]:
    """Replace external integrations with deterministic test doubles."""

    Base.metadata.create_all(application.state.container.engine)
    text_provider = FakeRecipeTextGenerationProvider(payload=build_generated_recipe_payload())
    image_provider = FakeRecipeImageGenerationProvider()
    object_storage = FakeObjectStorage()

    application.state.container.recipe_text_generation_provider = text_provider
    application.state.container.recipe_image_generation_provider = image_provider
    application.state.container.object_storage = object_storage
    application.state.container.distributed_lock_manager = FakeDistributedLockManager()
    application.state.container.admin_rate_limiter = NoopAdminRateLimiter()
    return text_provider, image_provider, object_storage


def build_admin_headers() -> dict[str, str]:
    """Build an authenticated admin header set for tests."""

    settings = get_settings()
    return {
        "Authorization": f"Bearer {settings.admin_bearer_token.get_secret_value()}",
        "Content-Type": "application/json",
    }


def test_admin_generation_happy_path_and_publication_flow() -> None:
    """Admin should be able to generate, publish and then expose a recipe publicly."""

    application = create_app()

    with TestClient(application) as client:
        text_provider, image_provider, object_storage = configure_test_container(application)
        headers = build_admin_headers()
        slot_time_utc = "2026-03-15T12:00:00+00:00"

        generation_response = client.post(
            "/api/v1/admin/generations/run-now",
            headers=headers,
            json={"slot_time_utc": slot_time_utc},
        )

        assert generation_response.status_code == 202
        generation_payload = generation_response.json()
        assert generation_payload["was_enqueued"] is True
        assert text_provider.call_count == 1
        assert image_provider.call_count == 1
        assert len(object_storage.objects) == 1

        job_id = UUID(generation_payload["job"]["id"])

        with application.state.container.session_factory() as session:
            recipe_repository = SqlAlchemyRecipeRepository(session=session)
            generation_job_repository = SqlAlchemyGenerationJobRepository(session=session)
            generation_job = generation_job_repository.get_by_id(job_id)

            assert generation_job is not None
            assert generation_job.status == "completed"
            recipe_id = UUID(generation_job.provider_response_metadata["recipe_id"])
            recipe_aggregate = recipe_repository.get_by_id(recipe_id)

            assert recipe_aggregate is not None
            assert recipe_aggregate.image is not None

        publish_response = client.post(
            f"/api/v1/admin/recipes/{recipe_id}/publish",
            headers=headers,
        )

        assert publish_response.status_code == 200
        publish_payload = publish_response.json()
        assert publish_payload["image"]["storage_key"]
        assert publish_payload["image"]["provider_name"] == "fake"

        latest_recipe_response = client.get("/api/v1/recipes/latest")
        assert latest_recipe_response.status_code == 200
        latest_recipe_payload = latest_recipe_response.json()
        assert latest_recipe_payload["id"] == str(recipe_id)
        assert latest_recipe_payload["title"] == "Сливочная паста с грибами"
        assert latest_recipe_payload["image"]["url"].startswith("https://example.test/")
        assert "storage_key" not in latest_recipe_payload["image"]
        assert "provider_name" not in latest_recipe_payload["image"]
        assert "image_prompt" not in latest_recipe_payload
        assert "source_generation_parameters" not in latest_recipe_payload


def test_admin_generation_returns_existing_result_for_same_slot() -> None:
    """The same slot should not regenerate content twice."""

    application = create_app()

    with TestClient(application) as client:
        text_provider, image_provider, _ = configure_test_container(application)
        headers = build_admin_headers()
        payload = {"slot_time_utc": "2026-03-15T13:00:00+00:00"}

        first_response = client.post(
            "/api/v1/admin/generations/run-now",
            headers=headers,
            json=payload,
        )
        second_response = client.post(
            "/api/v1/admin/generations/run-now",
            headers=headers,
            json=payload,
        )

        assert first_response.status_code == 202
        assert second_response.status_code == 202
        assert first_response.json()["was_enqueued"] is True
        assert second_response.json()["was_enqueued"] is False
        assert text_provider.call_count == 1
        assert image_provider.call_count == 1


def test_admin_generation_returns_conflict_when_lock_is_unavailable() -> None:
    """Lock acquisition failure should surface as HTTP 409."""

    application = create_app()

    with TestClient(application) as client:
        text_provider, image_provider, _ = configure_test_container(application)
        application.state.container.distributed_lock_manager = FakeDistributedLockManager(
            should_acquire=False
        )
        headers = build_admin_headers()

        response = client.post(
            "/api/v1/admin/generations/run-now",
            headers=headers,
            json={"slot_time_utc": "2026-03-15T14:00:00+00:00"},
        )

        assert response.status_code == 409
        assert text_provider.call_count == 0
        assert image_provider.call_count == 0


def test_admin_generation_rejects_naive_slot_time() -> None:
    """Manual generation should reject naive datetimes instead of guessing the host timezone."""

    application = create_app()

    with TestClient(application) as client:
        text_provider, image_provider, _ = configure_test_container(application)
        headers = build_admin_headers()

        response = client.post(
            "/api/v1/admin/generations/run-now",
            headers=headers,
            json={"slot_time_utc": "2026-03-15T14:00:00"},
        )

        assert response.status_code == 422
        assert text_provider.call_count == 0
        assert image_provider.call_count == 0
