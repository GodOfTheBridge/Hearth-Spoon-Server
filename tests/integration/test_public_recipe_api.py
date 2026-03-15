"""Integration tests for the public recipe endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from app.application.models import CreateRecipeCommand, CreateRecipeImageCommand
from app.domain.entities import GeneratedRecipePayload, RecipeGenerationParameters
from app.domain.enums import DifficultyLevel, ModerationStatus, PublicationStatus
from app.domain.time import get_current_utc_datetime
from app.infrastructure.database.base import Base
from app.infrastructure.database.repositories.recipe_repository import SqlAlchemyRecipeRepository
from app.main import create_app


def build_generated_recipe_payload(
    *,
    title: str = "Сливочная паста с грибами",
    subtitle: str = "Быстрый домашний ужин",
    story_or_intro: str = (
        "Нежная паста с насыщенным грибным вкусом для спокойного домашнего вечера."
    ),
) -> GeneratedRecipePayload:
    """Create a deterministic recipe payload."""

    return GeneratedRecipePayload.model_validate(
        {
            "title": title,
            "subtitle": subtitle,
            "story_or_intro": story_or_intro,
            "servings": 2,
            "preparation_time_minutes": 15,
            "cooking_time_minutes": 20,
            "difficulty_level": DifficultyLevel.EASY,
            "ingredients": [
                {"name": "Паста", "amount": "250", "unit": "г", "notes": ""},
                {"name": "Шампиньоны", "amount": "200", "unit": "г", "notes": "Нарезать"},
                {"name": "Сливки", "amount": "200", "unit": "мл", "notes": "20%"},
            ],
            "tools": ["кастрюля", "сковорода"],
            "steps": [
                {
                    "step_number": 1,
                    "title": "Подготовка",
                    "description": "Отварите пасту до состояния al dente.",
                    "duration_minutes": 10,
                    "temperature_celsius": None,
                    "warnings": [],
                },
                {
                    "step_number": 2,
                    "title": "Обжарка",
                    "description": "Обжарьте грибы до румяности.",
                    "duration_minutes": 7,
                    "temperature_celsius": 180,
                    "warnings": [],
                },
                {
                    "step_number": 3,
                    "title": "Соус",
                    "description": "Добавьте сливки и объедините все компоненты.",
                    "duration_minutes": 5,
                    "temperature_celsius": 90,
                    "warnings": [],
                },
            ],
            "cooking_tips": ["Не переваривайте пасту."],
            "plating_tips": ["Сверху добавьте свежемолотый перец."],
            "style_tags": ["comfort food", "weeknight dinner"],
            "image_generation_brief": "Тарелка сливочной пасты с грибами в мягком теплом свете.",
        }
    )


def seed_recipe(
    application,
    *,
    title: str = "Сливочная паста с грибами",
    subtitle: str = "Быстрый домашний ужин",
    story_or_intro: str = (
        "Нежная паста с насыщенным грибным вкусом для спокойного домашнего вечера."
    ),
    publication_status: PublicationStatus = PublicationStatus.PUBLISHED,
    published_at: datetime | None = None,
    storage_key: str = "recipes/test/latest.png",
) -> UUID:
    """Persist a recipe and image fixture into the test database."""

    with application.state.container.session_factory() as session:
        recipe_repository = SqlAlchemyRecipeRepository(session=session)
        recipe = recipe_repository.create_recipe(
            CreateRecipeCommand(
                generated_recipe=build_generated_recipe_payload(
                    title=title,
                    subtitle=subtitle,
                    story_or_intro=story_or_intro,
                ),
                source_generation_parameters=RecipeGenerationParameters(
                    language_code="ru-RU",
                    cuisine_context="home cooking",
                    dietary_context="balanced",
                    excluded_ingredients=[],
                    image_style="editorial food photography",
                    maximum_ingredients=12,
                    maximum_steps=8,
                ),
                image_prompt="A plated creamy pasta with mushrooms.",
                moderation_status=ModerationStatus.PENDING,
                publication_status=publication_status,
                published_at=published_at,
            )
        )
        recipe_repository.create_recipe_image(
            CreateRecipeImageCommand(
                recipe_id=recipe.id,
                storage_key=storage_key,
                public_url=f"https://cdn.example.test/{storage_key}",
                width=1024,
                height=1024,
                mime_type="image/png",
                provider_name="openai",
                provider_model="gpt-image-1.5",
            )
        )
        session.commit()
    return recipe.id


def test_latest_recipe_endpoint_returns_published_recipe() -> None:
    """The latest recipe endpoint should expose a published recipe."""

    application = create_app()

    with TestClient(application) as client:
        Base.metadata.create_all(application.state.container.engine)
        recipe_id = seed_recipe(
            application,
            published_at=get_current_utc_datetime(),
            storage_key="recipes/test/latest.png",
        )

        response = client.get("/api/v1/recipes/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(recipe_id)
    assert payload["title"] == "Сливочная паста с грибами"
    assert payload["image"]["url"].endswith("recipes/test/latest.png")
    assert "storage_key" not in payload["image"]
    assert "provider_name" not in payload["image"]
    assert "source_generation_parameters" not in payload
    assert "image_prompt" not in payload


def test_recipe_feed_endpoint_returns_published_feed() -> None:
    """The recipe feed endpoint should return published recipes in newest-first order."""

    application = create_app()

    with TestClient(application) as client:
        Base.metadata.create_all(application.state.container.engine)
        older_recipe_id = seed_recipe(
            application,
            title="Запеченная треска с лимоном",
            subtitle="Легкий ужин за 30 минут",
            story_or_intro="Нежная рыба с ярким цитрусовым ароматом и хрустящими овощами.",
            published_at=datetime(2026, 3, 15, 10, 0, tzinfo=UTC),
            storage_key="recipes/test/baked-cod.png",
        )
        newer_recipe_id = seed_recipe(
            application,
            published_at=datetime(2026, 3, 15, 12, 0, tzinfo=UTC),
            storage_key="recipes/test/latest.png",
        )

        response = client.get("/api/v1/recipes/feed", params={"limit": 20, "offset": 0})

    assert response.status_code == 200
    payload = response.json()
    assert payload["limit"] == 20
    assert payload["offset"] == 0
    assert [item["id"] for item in payload["items"]] == [str(newer_recipe_id), str(older_recipe_id)]
    assert payload["items"][0]["title"] == "Сливочная паста с грибами"
    assert payload["items"][1]["title"] == "Запеченная треска с лимоном"


def test_recipe_by_id_endpoint_returns_published_recipe() -> None:
    """The public recipe detail endpoint should return a published recipe by id."""

    application = create_app()

    with TestClient(application) as client:
        Base.metadata.create_all(application.state.container.engine)
        recipe_id = seed_recipe(
            application,
            published_at=get_current_utc_datetime(),
            storage_key="recipes/test/detail.png",
        )

        response = client.get(f"/api/v1/recipes/{recipe_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(recipe_id)
    assert payload["title"] == "Сливочная паста с грибами"
    assert payload["image"]["url"].endswith("recipes/test/detail.png")
    assert "storage_key" not in payload["image"]
