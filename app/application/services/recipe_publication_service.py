"""Admin operations for publication state changes."""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy.orm import Session

from app.application.exceptions import DatabaseOperationError
from app.application.ports.repositories import RecipeRepository
from app.domain.entities import RecipeAggregate
from app.domain.time import get_current_utc_datetime

logger = structlog.get_logger(__name__)


class RecipePublicationService:
    """Publish or unpublish recipes in an auditable way."""

    def __init__(self, *, recipe_repository: RecipeRepository, database_session: Session) -> None:
        self._recipe_repository = recipe_repository
        self._database_session = database_session

    def publish_recipe(self, *, recipe_id: UUID, admin_actor: str) -> RecipeAggregate:
        """Publish a recipe and emit an audit log entry."""

        try:
            self._recipe_repository.publish_recipe(
                recipe_id=recipe_id,
                published_at=get_current_utc_datetime(),
            )
            self._database_session.commit()
        except Exception:
            self._database_session.rollback()
            raise

        logger.info("admin.recipe.published", recipe_id=str(recipe_id), admin_actor=admin_actor)
        recipe_aggregate = self._recipe_repository.get_by_id(recipe_id)
        if recipe_aggregate is None:
            raise DatabaseOperationError(
                f"Recipe '{recipe_id}' was not found after publication commit."
            )
        return recipe_aggregate

    def unpublish_recipe(self, *, recipe_id: UUID, admin_actor: str) -> RecipeAggregate:
        """Unpublish a recipe and emit an audit log entry."""

        try:
            self._recipe_repository.unpublish_recipe(recipe_id=recipe_id)
            self._database_session.commit()
        except Exception:
            self._database_session.rollback()
            raise

        logger.info("admin.recipe.unpublished", recipe_id=str(recipe_id), admin_actor=admin_actor)
        recipe_aggregate = self._recipe_repository.get_by_id(recipe_id)
        if recipe_aggregate is None:
            raise DatabaseOperationError(
                f"Recipe '{recipe_id}' was not found after unpublication commit."
            )
        return recipe_aggregate
