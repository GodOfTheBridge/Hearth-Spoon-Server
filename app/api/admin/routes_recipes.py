"""Административные эндпоинты публикации рецептов."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Path

from app.api.dependencies import (
    get_container,
    get_recipe_publication_service,
    require_admin_write_access,
)
from app.api.schemas.recipe import RecipeDetailResponse
from app.bootstrap import ApplicationContainer
from app.security.auth import AdminIdentity

router = APIRouter(prefix="/admin/recipes", tags=["Администрирование"])


@router.post(
    "/{recipe_id}/publish",
    response_model=RecipeDetailResponse,
    summary="Опубликовать рецепт",
    description="Переводит рецепт в опубликованное состояние, если он готов к публикации.",
    response_description="Опубликованный рецепт.",
)
def publish_recipe(
    recipe_id: UUID = Path(description="Идентификатор рецепта."),
    admin_identity: AdminIdentity = Depends(require_admin_write_access),
    recipe_publication_service=Depends(get_recipe_publication_service),
    container: ApplicationContainer = Depends(get_container),
) -> RecipeDetailResponse:
    """Публикует рецепт."""

    recipe_aggregate = recipe_publication_service.publish_recipe(
        recipe_id=recipe_id,
        admin_actor=admin_identity.actor_id,
    )
    return RecipeDetailResponse.from_domain(recipe_aggregate, container.object_storage)


@router.post(
    "/{recipe_id}/unpublish",
    response_model=RecipeDetailResponse,
    summary="Снять рецепт с публикации",
    description="Переводит рецепт из опубликованного состояния обратно в непубличное.",
    response_description="Рецепт после снятия с публикации.",
)
def unpublish_recipe(
    recipe_id: UUID = Path(description="Идентификатор рецепта."),
    admin_identity: AdminIdentity = Depends(require_admin_write_access),
    recipe_publication_service=Depends(get_recipe_publication_service),
    container: ApplicationContainer = Depends(get_container),
) -> RecipeDetailResponse:
    """Снимает рецепт с публикации."""

    recipe_aggregate = recipe_publication_service.unpublish_recipe(
        recipe_id=recipe_id,
        admin_actor=admin_identity.actor_id,
    )
    return RecipeDetailResponse.from_domain(recipe_aggregate, container.object_storage)
