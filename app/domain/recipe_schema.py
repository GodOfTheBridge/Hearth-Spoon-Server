"""Strict JSON schema and Pydantic validation for generated recipe payloads."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.domain.constants import DEFAULT_SCHEMA_NAME
from app.domain.entities import GeneratedRecipePayload
from app.domain.exceptions import StructuredOutputValidationError

RECIPE_RESPONSE_JSON_SCHEMA: dict[str, Any] = {
    "name": DEFAULT_SCHEMA_NAME,
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"type": "string", "minLength": 3},
            "subtitle": {"type": "string", "minLength": 3},
            "story_or_intro": {"type": "string", "minLength": 20},
            "servings": {"type": "integer", "minimum": 1, "maximum": 12},
            "preparation_time_minutes": {"type": "integer", "minimum": 1, "maximum": 240},
            "cooking_time_minutes": {"type": "integer", "minimum": 1, "maximum": 360},
            "difficulty_level": {
                "type": "string",
                "enum": ["easy", "medium", "hard"],
            },
            "ingredients": {
                "type": "array",
                "minItems": 3,
                "maxItems": 20,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "amount": {"type": "string", "minLength": 1},
                        "unit": {"type": "string", "minLength": 1},
                        "notes": {"type": "string"},
                    },
                    "required": ["name", "amount", "unit", "notes"],
                },
            },
            "tools": {
                "type": "array",
                "minItems": 1,
                "maxItems": 12,
                "items": {"type": "string", "minLength": 1},
            },
            "steps": {
                "type": "array",
                "minItems": 3,
                "maxItems": 15,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "step_number": {"type": "integer", "minimum": 1},
                        "title": {"type": "string", "minLength": 1},
                        "description": {"type": "string", "minLength": 10},
                        "duration_minutes": {"type": "integer", "minimum": 1, "maximum": 180},
                        "temperature_celsius": {
                            "anyOf": [
                                {"type": "integer", "minimum": 30, "maximum": 350},
                                {"type": "null"},
                            ]
                        },
                        "warnings": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "step_number",
                        "title",
                        "description",
                        "duration_minutes",
                        "temperature_celsius",
                        "warnings",
                    ],
                },
            },
            "cooking_tips": {
                "type": "array",
                "items": {"type": "string"},
            },
            "plating_tips": {
                "type": "array",
                "items": {"type": "string"},
            },
            "style_tags": {
                "type": "array",
                "minItems": 1,
                "maxItems": 10,
                "items": {"type": "string"},
            },
            "image_generation_brief": {"type": "string", "minLength": 10},
        },
        "required": [
            "title",
            "subtitle",
            "story_or_intro",
            "servings",
            "preparation_time_minutes",
            "cooking_time_minutes",
            "difficulty_level",
            "ingredients",
            "tools",
            "steps",
            "cooking_tips",
            "plating_tips",
            "style_tags",
            "image_generation_brief",
        ],
    },
}


def validate_recipe_payload(raw_payload: dict[str, Any]) -> GeneratedRecipePayload:
    """Validate provider output with Pydantic after schema-constrained generation."""

    try:
        return GeneratedRecipePayload.model_validate(raw_payload)
    except ValidationError as error:
        raise StructuredOutputValidationError(
            "Provider returned invalid structured recipe payload."
        ) from error
