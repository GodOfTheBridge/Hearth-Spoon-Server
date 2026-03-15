"""Recipe API schemas and mappers."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.api.schemas.examples import (
    PUBLIC_RECIPE_DETAIL_EXAMPLE,
    PUBLIC_RECIPE_IMAGE_EXAMPLE,
    PUBLIC_RECIPE_SUMMARY_EXAMPLE,
    RECIPE_DETAIL_EXAMPLE,
    RECIPE_FEED_RESPONSE_EXAMPLE,
    RECIPE_GENERATION_PARAMETERS_EXAMPLE,
    RECIPE_IMAGE_EXAMPLE,
    RECIPE_INGREDIENT_EXAMPLE,
    RECIPE_STEP_EXAMPLE,
    RECIPE_SUMMARY_EXAMPLE,
)
from app.application.ports.storage import ObjectStorage
from app.domain.entities import (
    RecipeAggregate,
    RecipeGenerationParameters,
    RecipeImage,
    RecipeIngredient,
    RecipeStep,
)


class RecipeIngredientResponse(BaseModel):
    """Ingredient response item."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": RECIPE_INGREDIENT_EXAMPLE},
    )

    name: str
    amount: str
    unit: str
    notes: str

    @classmethod
    def from_domain(cls, ingredient: RecipeIngredient) -> RecipeIngredientResponse:
        return cls(**ingredient.model_dump())


class RecipeStepResponse(BaseModel):
    """Step response item."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": RECIPE_STEP_EXAMPLE},
    )

    step_number: int
    title: str
    description: str
    duration_minutes: int
    temperature_celsius: int | None = None
    warnings: list[str]

    @classmethod
    def from_domain(cls, recipe_step: RecipeStep) -> RecipeStepResponse:
        return cls(**recipe_step.model_dump())


class RecipeGenerationParametersResponse(BaseModel):
    """Generation parameter snapshot stored with a recipe."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": RECIPE_GENERATION_PARAMETERS_EXAMPLE},
    )

    language_code: str
    cuisine_context: str
    dietary_context: str
    excluded_ingredients: list[str]
    image_style: str
    maximum_ingredients: int
    maximum_steps: int

    @classmethod
    def from_domain(
        cls,
        parameters: RecipeGenerationParameters,
    ) -> RecipeGenerationParametersResponse:
        return cls(**parameters.model_dump())


class RecipeImageResponse(BaseModel):
    """Recipe image metadata exposed to clients."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": RECIPE_IMAGE_EXAMPLE})

    id: UUID
    storage_key: str
    url: str
    width: int | None = None
    height: int | None = None
    mime_type: str
    provider_name: str
    provider_model: str
    created_at: datetime

    @classmethod
    def from_domain(
        cls,
        recipe_image: RecipeImage,
        object_storage: ObjectStorage,
    ) -> RecipeImageResponse:
        image_url = recipe_image.public_url or object_storage.build_read_url(
            storage_key=recipe_image.storage_key
        )
        return cls(
            id=recipe_image.id,
            storage_key=recipe_image.storage_key,
            url=image_url,
            width=recipe_image.width,
            height=recipe_image.height,
            mime_type=recipe_image.mime_type,
            provider_name=recipe_image.provider_name,
            provider_model=recipe_image.provider_model,
            created_at=recipe_image.created_at,
        )


class PublicRecipeImageResponse(BaseModel):
    """Client-safe recipe image metadata exposed to public consumers."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": PUBLIC_RECIPE_IMAGE_EXAMPLE},
    )

    url: str
    width: int | None = None
    height: int | None = None
    mime_type: str

    @classmethod
    def from_domain(
        cls,
        recipe_image: RecipeImage,
        object_storage: ObjectStorage,
    ) -> PublicRecipeImageResponse:
        image_url = recipe_image.public_url or object_storage.build_read_url(
            storage_key=recipe_image.storage_key
        )
        return cls(
            url=image_url,
            width=recipe_image.width,
            height=recipe_image.height,
            mime_type=recipe_image.mime_type,
        )


class RecipeSummaryResponse(BaseModel):
    """Recipe summary response for feed endpoints."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": RECIPE_SUMMARY_EXAMPLE})

    id: UUID
    title: str
    subtitle: str
    story_or_intro: str
    servings: int
    cooking_time_minutes: int
    preparation_time_minutes: int
    difficulty_level: str
    style_tags: list[str]
    publication_status: str
    created_at: datetime
    published_at: datetime | None = None
    image: RecipeImageResponse | None = None

    @classmethod
    def from_domain(
        cls,
        recipe_aggregate: RecipeAggregate,
        object_storage: ObjectStorage,
    ) -> RecipeSummaryResponse:
        return cls(
            id=recipe_aggregate.recipe.id,
            title=recipe_aggregate.recipe.title,
            subtitle=recipe_aggregate.recipe.subtitle,
            story_or_intro=recipe_aggregate.recipe.story_or_intro,
            servings=recipe_aggregate.recipe.servings,
            cooking_time_minutes=recipe_aggregate.recipe.cooking_time_minutes,
            preparation_time_minutes=recipe_aggregate.recipe.preparation_time_minutes,
            difficulty_level=recipe_aggregate.recipe.difficulty_level,
            style_tags=recipe_aggregate.recipe.style_tags,
            publication_status=recipe_aggregate.recipe.publication_status,
            created_at=recipe_aggregate.recipe.created_at,
            published_at=recipe_aggregate.recipe.published_at,
            image=(
                RecipeImageResponse.from_domain(recipe_aggregate.image, object_storage)
                if recipe_aggregate.image
                else None
            ),
        )


class PublicRecipeSummaryResponse(BaseModel):
    """Client-safe recipe summary for public feed endpoints."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": PUBLIC_RECIPE_SUMMARY_EXAMPLE},
    )

    id: UUID
    title: str
    subtitle: str
    story_or_intro: str
    servings: int
    cooking_time_minutes: int
    preparation_time_minutes: int
    difficulty_level: str
    style_tags: list[str]
    published_at: datetime | None = None
    image: PublicRecipeImageResponse | None = None

    @classmethod
    def from_domain(
        cls,
        recipe_aggregate: RecipeAggregate,
        object_storage: ObjectStorage,
    ) -> PublicRecipeSummaryResponse:
        return cls(
            id=recipe_aggregate.recipe.id,
            title=recipe_aggregate.recipe.title,
            subtitle=recipe_aggregate.recipe.subtitle,
            story_or_intro=recipe_aggregate.recipe.story_or_intro,
            servings=recipe_aggregate.recipe.servings,
            cooking_time_minutes=recipe_aggregate.recipe.cooking_time_minutes,
            preparation_time_minutes=recipe_aggregate.recipe.preparation_time_minutes,
            difficulty_level=recipe_aggregate.recipe.difficulty_level,
            style_tags=recipe_aggregate.recipe.style_tags,
            published_at=recipe_aggregate.recipe.published_at,
            image=(
                PublicRecipeImageResponse.from_domain(recipe_aggregate.image, object_storage)
                if recipe_aggregate.image
                else None
            ),
        )


class RecipeDetailResponse(BaseModel):
    """Detailed recipe response for mobile clients."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": RECIPE_DETAIL_EXAMPLE})

    id: UUID
    title: str
    subtitle: str
    story_or_intro: str
    servings: int
    cooking_time_minutes: int
    preparation_time_minutes: int
    difficulty_level: str
    ingredients: list[RecipeIngredientResponse]
    tools: list[str]
    steps: list[RecipeStepResponse]
    cooking_tips: list[str]
    plating_tips: list[str]
    style_tags: list[str]
    source_generation_parameters: RecipeGenerationParametersResponse
    image_prompt: str
    moderation_status: str
    publication_status: str
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None
    image: RecipeImageResponse | None = None

    @classmethod
    def from_domain(
        cls,
        recipe_aggregate: RecipeAggregate,
        object_storage: ObjectStorage,
    ) -> RecipeDetailResponse:
        recipe = recipe_aggregate.recipe
        return cls(
            id=recipe.id,
            title=recipe.title,
            subtitle=recipe.subtitle,
            story_or_intro=recipe.story_or_intro,
            servings=recipe.servings,
            cooking_time_minutes=recipe.cooking_time_minutes,
            preparation_time_minutes=recipe.preparation_time_minutes,
            difficulty_level=recipe.difficulty_level,
            ingredients=[RecipeIngredientResponse.from_domain(item) for item in recipe.ingredients],
            tools=recipe.tools,
            steps=[RecipeStepResponse.from_domain(item) for item in recipe.steps],
            cooking_tips=recipe.cooking_tips,
            plating_tips=recipe.plating_tips,
            style_tags=recipe.style_tags,
            source_generation_parameters=RecipeGenerationParametersResponse.from_domain(
                recipe.source_generation_parameters
            ),
            image_prompt=recipe.image_prompt,
            moderation_status=recipe.moderation_status,
            publication_status=recipe.publication_status,
            created_at=recipe.created_at,
            updated_at=recipe.updated_at,
            published_at=recipe.published_at,
            image=(
                RecipeImageResponse.from_domain(recipe_aggregate.image, object_storage)
                if recipe_aggregate.image
                else None
            ),
        )


class PublicRecipeDetailResponse(BaseModel):
    """Client-safe detailed recipe response for public consumers."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": PUBLIC_RECIPE_DETAIL_EXAMPLE},
    )

    id: UUID
    title: str
    subtitle: str
    story_or_intro: str
    servings: int
    cooking_time_minutes: int
    preparation_time_minutes: int
    difficulty_level: str
    ingredients: list[RecipeIngredientResponse]
    tools: list[str]
    steps: list[RecipeStepResponse]
    cooking_tips: list[str]
    plating_tips: list[str]
    style_tags: list[str]
    published_at: datetime | None = None
    image: PublicRecipeImageResponse | None = None

    @classmethod
    def from_domain(
        cls,
        recipe_aggregate: RecipeAggregate,
        object_storage: ObjectStorage,
    ) -> PublicRecipeDetailResponse:
        recipe = recipe_aggregate.recipe
        return cls(
            id=recipe.id,
            title=recipe.title,
            subtitle=recipe.subtitle,
            story_or_intro=recipe.story_or_intro,
            servings=recipe.servings,
            cooking_time_minutes=recipe.cooking_time_minutes,
            preparation_time_minutes=recipe.preparation_time_minutes,
            difficulty_level=recipe.difficulty_level,
            ingredients=[RecipeIngredientResponse.from_domain(item) for item in recipe.ingredients],
            tools=recipe.tools,
            steps=[RecipeStepResponse.from_domain(item) for item in recipe.steps],
            cooking_tips=recipe.cooking_tips,
            plating_tips=recipe.plating_tips,
            style_tags=recipe.style_tags,
            published_at=recipe.published_at,
            image=(
                PublicRecipeImageResponse.from_domain(recipe_aggregate.image, object_storage)
                if recipe_aggregate.image
                else None
            ),
        )


class RecipeFeedResponse(BaseModel):
    """Public recipe feed payload."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": RECIPE_FEED_RESPONSE_EXAMPLE},
    )

    items: list[PublicRecipeSummaryResponse]
    limit: int
    offset: int
