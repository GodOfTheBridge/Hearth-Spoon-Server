"""Public recipe endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_container, get_recipe_query_service
from app.api.schemas.recipe import (
    PublicRecipeDetailResponse,
    PublicRecipeSummaryResponse,
    RecipeFeedResponse,
)
from app.bootstrap import ApplicationContainer

router = APIRouter(prefix="/recipes", tags=["public"])


@router.get("/latest", response_model=PublicRecipeDetailResponse)
def get_latest_recipe(
    recipe_query_service=Depends(get_recipe_query_service),
    container: ApplicationContainer = Depends(get_container),
) -> PublicRecipeDetailResponse:
    """Return the latest published recipe."""

    recipe_aggregate = recipe_query_service.get_latest_published_recipe()
    return PublicRecipeDetailResponse.from_domain(recipe_aggregate, container.object_storage)


@router.get("/feed", response_model=RecipeFeedResponse)
def get_recipe_feed(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of published recipes to return.",
        examples=[20],
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Zero-based number of published recipes to skip.",
        examples=[0],
    ),
    recipe_query_service=Depends(get_recipe_query_service),
    container: ApplicationContainer = Depends(get_container),
) -> RecipeFeedResponse:
    """Return a paginated feed of published recipes."""

    recipe_aggregates = recipe_query_service.get_published_feed(limit=limit, offset=offset)
    return RecipeFeedResponse(
        items=[
            PublicRecipeSummaryResponse.from_domain(recipe_aggregate, container.object_storage)
            for recipe_aggregate in recipe_aggregates
        ],
        limit=limit,
        offset=offset,
    )


@router.get("/{recipe_id}", response_model=PublicRecipeDetailResponse)
def get_recipe_by_id(
    recipe_id: UUID,
    recipe_query_service=Depends(get_recipe_query_service),
    container: ApplicationContainer = Depends(get_container),
) -> PublicRecipeDetailResponse:
    """Return a published recipe by identifier."""

    recipe_aggregate = recipe_query_service.get_published_recipe_by_id(recipe_id)
    return PublicRecipeDetailResponse.from_domain(recipe_aggregate, container.object_storage)
