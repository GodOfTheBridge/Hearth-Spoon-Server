"""Read-only recipe queries for public clients."""

from __future__ import annotations

from uuid import UUID

from app.application.exceptions import NotFoundError
from app.application.ports.repositories import RecipeRepository
from app.domain.entities import RecipeAggregate


class RecipeQueryService:
    """Expose public recipe read models through a small, explicit surface."""

    def __init__(self, *, recipe_repository: RecipeRepository) -> None:
        self._recipe_repository = recipe_repository

    def get_latest_published_recipe(self) -> RecipeAggregate:
        """Return the latest published recipe or raise a clear not-found error."""

        recipe_aggregate = self._recipe_repository.get_latest_published()
        if recipe_aggregate is None:
            raise NotFoundError("No published recipes are available yet.")
        return recipe_aggregate

    def get_published_feed(self, *, limit: int, offset: int) -> list[RecipeAggregate]:
        """Return the public recipe feed."""

        return self._recipe_repository.list_published_feed(limit=limit, offset=offset)

    def get_published_recipe_by_id(self, recipe_id: UUID) -> RecipeAggregate:
        """Return a published recipe by identifier or raise a not-found error."""

        recipe_aggregate = self._recipe_repository.get_published_by_id(recipe_id)
        if recipe_aggregate is None:
            raise NotFoundError(f"Published recipe '{recipe_id}' was not found.")
        return recipe_aggregate
