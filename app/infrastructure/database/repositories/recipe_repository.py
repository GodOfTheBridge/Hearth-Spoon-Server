"""Concrete recipe repository implementation."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.application.models import CreateRecipeCommand, CreateRecipeImageCommand
from app.application.ports.repositories import RecipeRepository
from app.domain.entities import Recipe, RecipeAggregate
from app.domain.enums import PublicationStatus
from app.domain.exceptions import NotFoundError
from app.infrastructure.database.mappers import map_recipe_aggregate, map_recipe_model_to_domain
from app.infrastructure.database.models import RecipeModel


class SqlAlchemyRecipeRepository(RecipeRepository):
    """SQLAlchemy-backed recipe repository."""

    def __init__(self, *, session: Session) -> None:
        self._session = session

    def get_latest_published(self) -> RecipeAggregate | None:
        """Return the latest published recipe aggregate."""

        statement = (
            select(RecipeModel)
            .options(joinedload(RecipeModel.image))
            .where(RecipeModel.publication_status == PublicationStatus.PUBLISHED)
            .order_by(RecipeModel.published_at.desc().nullslast(), RecipeModel.created_at.desc())
            .limit(1)
        )
        recipe_model = self._session.execute(statement).scalars().first()
        if recipe_model is None:
            return None
        return map_recipe_aggregate(recipe_model, recipe_model.image)

    def list_published_feed(self, *, limit: int, offset: int) -> list[RecipeAggregate]:
        """Return a page of published recipes."""

        statement = (
            select(RecipeModel)
            .options(joinedload(RecipeModel.image))
            .where(RecipeModel.publication_status == PublicationStatus.PUBLISHED)
            .order_by(RecipeModel.published_at.desc().nullslast(), RecipeModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        recipe_models = self._session.execute(statement).unique().scalars().all()
        return [map_recipe_aggregate(recipe_model, recipe_model.image) for recipe_model in recipe_models]

    def get_published_by_id(self, recipe_id: UUID) -> RecipeAggregate | None:
        """Return a published recipe by identifier."""

        statement = (
            select(RecipeModel)
            .options(joinedload(RecipeModel.image))
            .where(
                RecipeModel.id == recipe_id,
                RecipeModel.publication_status == PublicationStatus.PUBLISHED,
            )
        )
        recipe_model = self._session.execute(statement).unique().scalars().first()
        if recipe_model is None:
            return None
        return map_recipe_aggregate(recipe_model, recipe_model.image)

    def get_by_id(self, recipe_id: UUID) -> RecipeAggregate | None:
        """Return a recipe aggregate by identifier."""

        statement = (
            select(RecipeModel)
            .options(joinedload(RecipeModel.image))
            .where(RecipeModel.id == recipe_id)
        )
        recipe_model = self._session.execute(statement).unique().scalars().first()
        if recipe_model is None:
            return None
        return map_recipe_aggregate(recipe_model, recipe_model.image)

    def create_recipe(self, command: CreateRecipeCommand) -> Recipe:
        """Persist a generated recipe."""

        recipe_model = RecipeModel(
            title=command.generated_recipe.title,
            subtitle=command.generated_recipe.subtitle,
            story_or_intro=command.generated_recipe.story_or_intro,
            servings=command.generated_recipe.servings,
            cooking_time_minutes=command.generated_recipe.cooking_time_minutes,
            preparation_time_minutes=command.generated_recipe.preparation_time_minutes,
            difficulty_level=command.generated_recipe.difficulty_level,
            ingredients=[ingredient.model_dump(mode="json") for ingredient in command.generated_recipe.ingredients],
            tools=command.generated_recipe.tools,
            steps=[step.model_dump(mode="json") for step in command.generated_recipe.steps],
            cooking_tips=command.generated_recipe.cooking_tips,
            plating_tips=command.generated_recipe.plating_tips,
            style_tags=command.generated_recipe.style_tags,
            source_generation_parameters=command.source_generation_parameters.model_dump(mode="json"),
            image_prompt=command.image_prompt,
            moderation_status=command.moderation_status,
            publication_status=command.publication_status,
            published_at=command.published_at,
        )
        self._session.add(recipe_model)
        self._session.flush()
        return map_recipe_model_to_domain(recipe_model)

    def create_recipe_image(self, command: CreateRecipeImageCommand) -> None:
        """Persist image metadata for a recipe."""

        recipe_image_model = RecipeImageModel(
            recipe_id=command.recipe_id,
            storage_key=command.storage_key,
            public_url=command.public_url,
            width=command.width,
            height=command.height,
            mime_type=command.mime_type,
            provider_name=command.provider_name,
            provider_model=command.provider_model,
        )
        self._session.add(recipe_image_model)
        self._session.flush()

    def publish_recipe(self, recipe_id: UUID, published_at: datetime) -> Recipe:
        """Publish a recipe."""

        recipe_model = self._session.get(RecipeModel, recipe_id)
        if recipe_model is None:
            raise NotFoundError(f"Recipe '{recipe_id}' was not found.")

        recipe_model.publication_status = PublicationStatus.PUBLISHED
        recipe_model.published_at = published_at
        self._session.flush()
        return map_recipe_model_to_domain(recipe_model)

    def unpublish_recipe(self, recipe_id: UUID) -> Recipe:
        """Unpublish a recipe."""

        recipe_model = self._session.get(RecipeModel, recipe_id)
        if recipe_model is None:
            raise NotFoundError(f"Recipe '{recipe_id}' was not found.")

        recipe_model.publication_status = PublicationStatus.UNPUBLISHED
        recipe_model.published_at = None
        self._session.flush()
        return map_recipe_model_to_domain(recipe_model)
