"""Shared OpenAPI examples for request and response schemas."""

from __future__ import annotations

API_ERROR_EXAMPLE = {
    "detail": "Invalid admin bearer token.",
    "request_id": "f5990f1b0d804bdeac8f0f0c76cd8fc1",
}

RUN_GENERATION_NOW_REQUEST_EXAMPLE = {
    "slot_time_utc": "2026-03-15T12:00:00+00:00",
}

GENERATION_JOB_EXAMPLE = {
    "id": "b6f2fffb-a3aa-4d0d-9dd0-4f9326d16296",
    "job_type": "hourly_recipe_generation",
    "schedule_slot": "2026-03-15T12:00:00+00:00",
    "idempotency_key": "hourly-recipe:2026-03-15T12:00:00+00:00",
    "status": "completed",
    "started_at": "2026-03-15T12:00:05+00:00",
    "finished_at": "2026-03-15T12:00:29+00:00",
    "error_message": None,
    "retry_count": 0,
    "created_at": "2026-03-15T12:00:04+00:00",
}

RUN_GENERATION_NOW_RESPONSE_EXAMPLE = {
    "slot_time_utc": "2026-03-15T12:00:00+00:00",
    "job": GENERATION_JOB_EXAMPLE,
    "recipe_id": "4145fce8-e4aa-4384-8d0f-c145d43b8341",
    "was_enqueued": False,
    "message": "Generation for this slot has already completed.",
}

HEALTH_COMPONENT_EXAMPLE = {
    "status": "healthy",
}

HEALTH_RESPONSE_EXAMPLE = {
    "status": "healthy",
    "timestamp_utc": "2026-03-15T12:00:00+00:00",
    "components": {
        "database": {"status": "healthy"},
        "redis": {"status": "healthy"},
        "storage": {"status": "healthy"},
    },
}

PUBLIC_HEALTH_RESPONSE_EXAMPLE = {
    "status": "healthy",
    "timestamp_utc": "2026-03-15T12:00:00+00:00",
}

RECIPE_INGREDIENT_EXAMPLE = {
    "name": "Спагетти",
    "amount": "250",
    "unit": "г",
    "notes": "Из твердых сортов пшеницы.",
}

RECIPE_STEP_EXAMPLE = {
    "step_number": 1,
    "title": "Подготовьте пасту",
    "description": "Отварите пасту в подсоленной воде до состояния al dente.",
    "duration_minutes": 10,
    "temperature_celsius": None,
    "warnings": ["Не переварите пасту."],
}

RECIPE_GENERATION_PARAMETERS_EXAMPLE = {
    "language_code": "ru-RU",
    "cuisine_context": "modern home cooking",
    "dietary_context": "balanced",
    "excluded_ingredients": ["арахис"],
    "image_style": "editorial food photography",
    "maximum_ingredients": 14,
    "maximum_steps": 8,
}

RECIPE_IMAGE_EXAMPLE = {
    "id": "aa10a866-b936-4180-86a7-65b1865f7f1c",
    "storage_key": "recipes/2026/03/15/creamy-mushroom-pasta.png",
    "url": "https://cdn.example.test/recipes/2026/03/15/creamy-mushroom-pasta.png",
    "width": 1024,
    "height": 1024,
    "mime_type": "image/png",
    "provider_name": "openai",
    "provider_model": "gpt-image-1.5",
    "created_at": "2026-03-15T12:00:28+00:00",
}

PUBLIC_RECIPE_IMAGE_EXAMPLE = {
    "url": "https://cdn.example.test/recipes/2026/03/15/creamy-mushroom-pasta.png",
    "width": 1024,
    "height": 1024,
    "mime_type": "image/png",
}

RECIPE_SUMMARY_EXAMPLE = {
    "id": "4145fce8-e4aa-4384-8d0f-c145d43b8341",
    "title": "Сливочная паста с грибами",
    "subtitle": "Быстрый домашний ужин на каждый день",
    "story_or_intro": "Нежная паста с насыщенным грибным вкусом и мягким сливочным соусом.",
    "servings": 2,
    "cooking_time_minutes": 20,
    "preparation_time_minutes": 15,
    "difficulty_level": "easy",
    "style_tags": ["comfort food", "weeknight dinner"],
    "publication_status": "published",
    "created_at": "2026-03-15T12:00:20+00:00",
    "published_at": "2026-03-15T12:05:00+00:00",
    "image": RECIPE_IMAGE_EXAMPLE,
}

PUBLIC_RECIPE_SUMMARY_EXAMPLE = {
    "id": "4145fce8-e4aa-4384-8d0f-c145d43b8341",
    "title": "Сливочная паста с грибами",
    "subtitle": "Быстрый домашний ужин на каждый день",
    "story_or_intro": "Нежная паста с насыщенным грибным вкусом и мягким сливочным соусом.",
    "servings": 2,
    "cooking_time_minutes": 20,
    "preparation_time_minutes": 15,
    "difficulty_level": "easy",
    "style_tags": ["comfort food", "weeknight dinner"],
    "published_at": "2026-03-15T12:05:00+00:00",
    "image": PUBLIC_RECIPE_IMAGE_EXAMPLE,
}

RECIPE_DETAIL_EXAMPLE = {
    "id": "4145fce8-e4aa-4384-8d0f-c145d43b8341",
    "title": "Сливочная паста с грибами",
    "subtitle": "Быстрый домашний ужин на каждый день",
    "story_or_intro": "Нежная паста с насыщенным грибным вкусом и мягким сливочным соусом.",
    "servings": 2,
    "cooking_time_minutes": 20,
    "preparation_time_minutes": 15,
    "difficulty_level": "easy",
    "ingredients": [
        RECIPE_INGREDIENT_EXAMPLE,
        {
            "name": "Шампиньоны",
            "amount": "200",
            "unit": "г",
            "notes": "Нарезать пластинами.",
        },
    ],
    "tools": ["кастрюля", "сковорода"],
    "steps": [
        RECIPE_STEP_EXAMPLE,
        {
            "step_number": 2,
            "title": "Соберите соус",
            "description": "Обжарьте грибы, добавьте сливки и соедините все с пастой.",
            "duration_minutes": 10,
            "temperature_celsius": 180,
            "warnings": [],
        },
    ],
    "cooking_tips": ["Оставьте немного воды от пасты, чтобы регулировать густоту соуса."],
    "plating_tips": ["Подавайте с черным перцем и тертым пармезаном."],
    "style_tags": ["comfort food", "weeknight dinner"],
    "source_generation_parameters": RECIPE_GENERATION_PARAMETERS_EXAMPLE,
    "image_prompt": "A plated creamy mushroom pasta in warm editorial lighting.",
    "moderation_status": "pending",
    "publication_status": "published",
    "created_at": "2026-03-15T12:00:20+00:00",
    "updated_at": "2026-03-15T12:05:00+00:00",
    "published_at": "2026-03-15T12:05:00+00:00",
    "image": RECIPE_IMAGE_EXAMPLE,
}

PUBLIC_RECIPE_DETAIL_EXAMPLE = {
    "id": "4145fce8-e4aa-4384-8d0f-c145d43b8341",
    "title": "Сливочная паста с грибами",
    "subtitle": "Быстрый домашний ужин на каждый день",
    "story_or_intro": "Нежная паста с насыщенным грибным вкусом и мягким сливочным соусом.",
    "servings": 2,
    "cooking_time_minutes": 20,
    "preparation_time_minutes": 15,
    "difficulty_level": "easy",
    "ingredients": RECIPE_DETAIL_EXAMPLE["ingredients"],
    "tools": RECIPE_DETAIL_EXAMPLE["tools"],
    "steps": RECIPE_DETAIL_EXAMPLE["steps"],
    "cooking_tips": RECIPE_DETAIL_EXAMPLE["cooking_tips"],
    "plating_tips": RECIPE_DETAIL_EXAMPLE["plating_tips"],
    "style_tags": RECIPE_DETAIL_EXAMPLE["style_tags"],
    "published_at": "2026-03-15T12:05:00+00:00",
    "image": PUBLIC_RECIPE_IMAGE_EXAMPLE,
}

RECIPE_FEED_RESPONSE_EXAMPLE = {
    "items": [
        PUBLIC_RECIPE_SUMMARY_EXAMPLE,
        {
            "id": "5fe073bb-43d0-4536-9d16-1d1b43a4693d",
            "title": "Запеченная треска с лимоном",
            "subtitle": "Легкий ужин за 30 минут",
            "story_or_intro": "Нежная рыба с ярким цитрусовым ароматом и хрустящими овощами.",
            "servings": 3,
            "cooking_time_minutes": 25,
            "preparation_time_minutes": 10,
            "difficulty_level": "easy",
            "style_tags": ["seafood", "light dinner"],
            "published_at": "2026-03-15T10:00:00+00:00",
            "image": {
                "url": "https://cdn.example.test/recipes/2026/03/15/baked-cod.png",
                "width": 1024,
                "height": 1024,
                "mime_type": "image/png",
            },
        },
    ],
    "limit": 20,
    "offset": 0,
}
