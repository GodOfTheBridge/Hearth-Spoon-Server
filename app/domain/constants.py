"""Domain-level constants that should not be duplicated across layers."""

from __future__ import annotations

GENERATION_LOCK_KEY_PREFIX = "recipe-generation-slot"
RECIPE_IMAGE_STORAGE_PREFIX = "recipes"
OPENAI_PROVIDER_NAME = "openai"
DEFAULT_GENERATION_TYPE = "hourly_recipe"
DEFAULT_JOB_TYPE = "hourly_recipe_generation"
DEFAULT_SCHEMA_NAME = "recipe_generation"
JSON_CONTENT_TYPE = "application/json"
