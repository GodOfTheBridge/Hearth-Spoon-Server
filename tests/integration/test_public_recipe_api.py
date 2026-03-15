"""Integration test for the public recipe endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.application.models import CreateRecipeCommand, CreateRecipeImageCommand
from app.domain.entities import GeneratedRecipePayload, RecipeGenerationParameters
from app.domain.enums import DifficultyLevel, ModerationStatus, PublicationStatus
from app.domain.time import get_current_utc_datetime
from app.infrastructure.database.base import Base
from app.infrastructure.database.repositories.recipe_repository import SqlAlchemyRecipeRepository
from app.main import create_app


def build_generated_recipe_payload() -> GeneratedRecipePayload:
    """Create a deterministic recipe payload."""

    return GeneratedRecipePayload.model_validate(
        {
            "title": "Сливочная паста с грибами",
            "subtitle": "Быстрый домашний ужин",
            "story_or_intro": "Нежная паста с насыщенным грибным вкусом для спокойного домашнего вечера.",
            "servings": 2,
            "preparation_time_minutes": 15,
            "cooking_time_minutes": 20,
            "difficulty_level": DifficultyLevel.EASY,
            "ingredients": [
                {"name": "Паста", "amount": "250", "unit": "г", "notes": ""},
                {"name": "Шампиньоны", "amount": "200", "unit": "г", "notes": "нарезать"},
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


def test_latest_recipe_endpoint_returns_published_recipe() -> None:
    """The latest recipe endpoint should expose a published recipe."""

    application = create_app()

    with TestClient(application) as client:
        Base.metadata.create_all(application.state.container.engine)
        with application.state.container.session_factory() as session:
            recipe_repository = SqlAlchemyRecipeRepository(session=session)
            recipe = recipe_repository.create_recipe(
                CreateRecipeCommand(
                    generated_recipe=build_generated_recipe_payload(),
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
                    publication_status=PublicationStatus.PUBLISHED,
                    published_at=get_current_utc_datetime(),
                )
            )
            recipe_repository.create_recipe_image(
                CreateRecipeImageCommand(
                    recipe_id=recipe.id,
                    storage_key="recipes/test/latest.png",
                    public_url="https://cdn.example.test/recipes/test/latest.png",
                    width=1024,
                    height=1024,
                    mime_type="image/png",
                    provider_name="openai",
                    provider_model="gpt-image-1.5",
                )
            )
            session.commit()

        response = client.get("/api/v1/recipes/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Сливочная паста с грибами"
    assert payload["image"]["url"].endswith("recipes/test/latest.png")
