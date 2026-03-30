"""Публичные эндпоинты рецептов."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query

from app.api.dependencies import get_container, get_recipe_query_service
from app.api.schemas.recipe import (
    PublicRecipeDetailResponse,
    PublicRecipeSummaryResponse,
    RecipeFeedResponse,
)
from app.bootstrap import ApplicationContainer

router = APIRouter(prefix="/recipes", tags=["Публичное API"])


@router.get(
    "/latest",
    response_model=PublicRecipeDetailResponse,
    summary="Получить последний опубликованный рецепт",
    description="Возвращает последний опубликованный рецепт в клиентобезопасном формате.",
    response_description="Последний опубликованный рецепт.",
)
def get_latest_recipe(
    recipe_query_service=Depends(get_recipe_query_service),
    container: ApplicationContainer = Depends(get_container),
) -> PublicRecipeDetailResponse:
    """Возвращает последний опубликованный рецепт."""

    recipe_aggregate = recipe_query_service.get_latest_published_recipe()
    return PublicRecipeDetailResponse.from_domain(recipe_aggregate, container.object_storage)


@router.get(
    "/feed",
    response_model=RecipeFeedResponse,
    summary="Получить ленту опубликованных рецептов",
    description="Возвращает страницу ленты опубликованных рецептов с поддержкой пагинации.",
    response_description="Страница ленты опубликованных рецептов.",
)
def get_recipe_feed(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Максимальное количество опубликованных рецептов в ответе.",
        examples=[20],
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Смещение от начала ленты в опубликованных рецептах, начиная с нуля.",
        examples=[0],
    ),
    recipe_query_service=Depends(get_recipe_query_service),
    container: ApplicationContainer = Depends(get_container),
) -> RecipeFeedResponse:
    """Возвращает пагинируемую ленту опубликованных рецептов."""

    recipe_aggregates = recipe_query_service.get_published_feed(limit=limit, offset=offset)
    return RecipeFeedResponse(
        items=[
            PublicRecipeSummaryResponse.from_domain(recipe_aggregate, container.object_storage)
            for recipe_aggregate in recipe_aggregates
        ],
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{recipe_id}",
    response_model=PublicRecipeDetailResponse,
    summary="Получить опубликованный рецепт по идентификатору",
    description=(
        "Возвращает опубликованный рецепт по его идентификатору "
        "в клиентобезопасном формате."
    ),
    response_description="Опубликованный рецепт.",
)
def get_recipe_by_id(
    recipe_id: UUID = Path(description="Идентификатор опубликованного рецепта."),
    recipe_query_service=Depends(get_recipe_query_service),
    container: ApplicationContainer = Depends(get_container),
) -> PublicRecipeDetailResponse:
    """Возвращает опубликованный рецепт по идентификатору."""

    recipe_aggregate = recipe_query_service.get_published_recipe_by_id(recipe_id)
    return PublicRecipeDetailResponse.from_domain(recipe_aggregate, container.object_storage)
