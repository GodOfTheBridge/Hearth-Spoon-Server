"""Mapping between ORM records and domain entities."""

from __future__ import annotations

from app.domain.entities import (
    GenerationJob,
    GenerationScheduleSlot,
    Recipe,
    RecipeAggregate,
    RecipeGenerationParameters,
    RecipeImage,
)
from app.infrastructure.database.models import (
    GenerationJobModel,
    GenerationScheduleSlotModel,
    RecipeImageModel,
    RecipeModel,
)


def map_recipe_model_to_domain(recipe_model: RecipeModel) -> Recipe:
    """Convert a recipe ORM model into a domain entity."""

    return Recipe.model_validate(
        {
            "id": recipe_model.id,
            "title": recipe_model.title,
            "subtitle": recipe_model.subtitle,
            "story_or_intro": recipe_model.story_or_intro,
            "servings": recipe_model.servings,
            "cooking_time_minutes": recipe_model.cooking_time_minutes,
            "preparation_time_minutes": recipe_model.preparation_time_minutes,
            "difficulty_level": recipe_model.difficulty_level,
            "ingredients": recipe_model.ingredients,
            "tools": recipe_model.tools,
            "steps": recipe_model.steps,
            "cooking_tips": recipe_model.cooking_tips,
            "plating_tips": recipe_model.plating_tips,
            "style_tags": recipe_model.style_tags,
            "source_generation_parameters": RecipeGenerationParameters.model_validate(
                recipe_model.source_generation_parameters
            ),
            "image_prompt": recipe_model.image_prompt,
            "moderation_status": recipe_model.moderation_status,
            "publication_status": recipe_model.publication_status,
            "created_at": recipe_model.created_at,
            "updated_at": recipe_model.updated_at,
            "published_at": recipe_model.published_at,
        }
    )


def map_recipe_image_model_to_domain(recipe_image_model: RecipeImageModel) -> RecipeImage:
    """Convert image ORM metadata into a domain entity."""

    return RecipeImage.model_validate(recipe_image_model)


def map_recipe_aggregate(
    recipe_model: RecipeModel,
    recipe_image_model: RecipeImageModel | None,
) -> RecipeAggregate:
    """Map recipe and optional image into a domain aggregate."""

    return RecipeAggregate(
        recipe=map_recipe_model_to_domain(recipe_model),
        image=map_recipe_image_model_to_domain(recipe_image_model) if recipe_image_model else None,
    )


def map_generation_schedule_slot_model_to_domain(
    slot_model: GenerationScheduleSlotModel,
) -> GenerationScheduleSlot:
    """Convert slot ORM metadata into a domain entity."""

    return GenerationScheduleSlot.model_validate(slot_model)


def map_generation_job_model_to_domain(job_model: GenerationJobModel) -> GenerationJob:
    """Convert a job ORM model into a domain entity."""

    return GenerationJob.model_validate(
        {
            "id": job_model.id,
            "job_type": job_model.job_type,
            "schedule_slot": job_model.schedule_slot.slot_time_utc,
            "idempotency_key": job_model.idempotency_key,
            "status": job_model.status,
            "started_at": job_model.started_at,
            "finished_at": job_model.finished_at,
            "error_message": job_model.error_message,
            "retry_count": job_model.retry_count,
            "provider_request_metadata": job_model.provider_request_metadata or {},
            "provider_response_metadata": job_model.provider_response_metadata or {},
            "created_at": job_model.created_at,
        }
    )
