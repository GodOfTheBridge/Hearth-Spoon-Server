"""Admin recipe publication endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import get_container, get_recipe_publication_service, require_admin_access
from app.api.schemas.recipe import RecipeDetailResponse
from app.bootstrap import ApplicationContainer
from app.security.auth import AdminIdentity

router = APIRouter(prefix="/admin/recipes", tags=["admin-recipes"])


@router.post("/{recipe_id}/publish", response_model=RecipeDetailResponse)
def publish_recipe(
    recipe_id: UUID,
    admin_identity: AdminIdentity = Depends(require_admin_access),
    recipe_publication_service=Depends(get_recipe_publication_service),
    container: ApplicationContainer = Depends(get_container),
) -> RecipeDetailResponse:
    """Publish a recipe."""

    recipe_aggregate = recipe_publication_service.publish_recipe(
        recipe_id=recipe_id,
        admin_actor=admin_identity.actor_id,
    )
    return RecipeDetailResponse.from_domain(recipe_aggregate, container.object_storage)


@router.post("/{recipe_id}/unpublish", response_model=RecipeDetailResponse)
def unpublish_recipe(
    recipe_id: UUID,
    admin_identity: AdminIdentity = Depends(require_admin_access),
    recipe_publication_service=Depends(get_recipe_publication_service),
    container: ApplicationContainer = Depends(get_container),
) -> RecipeDetailResponse:
    """Unpublish a recipe."""

    recipe_aggregate = recipe_publication_service.unpublish_recipe(
        recipe_id=recipe_id,
        admin_actor=admin_identity.actor_id,
    )
    return RecipeDetailResponse.from_domain(recipe_aggregate, container.object_storage)
