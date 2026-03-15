"""Centralized runtime settings with strict validation."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="ПечьДаЛожка Backend", validation_alias=AliasChoices("APP_NAME"))
    app_environment: str = Field(
        default="development", validation_alias=AliasChoices("APP_ENVIRONMENT")
    )
    app_debug: bool = Field(default=False, validation_alias=AliasChoices("APP_DEBUG"))
    app_host: str = Field(default="0.0.0.0", validation_alias=AliasChoices("APP_HOST"))
    app_port: int = Field(default=8000, validation_alias=AliasChoices("APP_PORT"))
    log_level: str = Field(default="INFO", validation_alias=AliasChoices("LOG_LEVEL"))

    database_url: str = Field(validation_alias=AliasChoices("DATABASE_URL"))
    redis_url: str = Field(validation_alias=AliasChoices("REDIS_URL"))

    s3_endpoint_url: str = Field(validation_alias=AliasChoices("S3_ENDPOINT_URL"))
    s3_region_name: str = Field(
        default="us-east-1", validation_alias=AliasChoices("S3_REGION_NAME")
    )
    s3_bucket_name: str = Field(validation_alias=AliasChoices("S3_BUCKET_NAME"))
    s3_access_key_id: str = Field(validation_alias=AliasChoices("S3_ACCESS_KEY_ID"))
    s3_secret_access_key: SecretStr = Field(validation_alias=AliasChoices("S3_SECRET_ACCESS_KEY"))
    s3_use_ssl: bool = Field(default=False, validation_alias=AliasChoices("S3_USE_SSL"))
    s3_public_base_url: str | None = Field(
        default=None, validation_alias=AliasChoices("S3_PUBLIC_BASE_URL")
    )
    s3_public_endpoint_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("S3_PUBLIC_ENDPOINT_URL"),
    )
    s3_presigned_url_expiration_seconds: int = Field(
        default=900,
        validation_alias=AliasChoices("S3_PRESIGNED_URL_EXPIRATION_SECONDS"),
    )

    openai_api_key: SecretStr = Field(validation_alias=AliasChoices("OPENAI_API_KEY"))
    openai_project_id: str | None = Field(
        default=None, validation_alias=AliasChoices("OPENAI_PROJECT_ID")
    )
    openai_text_model: str = Field(
        default="gpt-5-mini", validation_alias=AliasChoices("OPENAI_TEXT_MODEL")
    )
    openai_image_model: str = Field(
        default="gpt-image-1.5",
        validation_alias=AliasChoices("OPENAI_IMAGE_MODEL"),
    )
    openai_text_timeout_seconds: int = Field(
        default=60,
        validation_alias=AliasChoices("OPENAI_TEXT_TIMEOUT_SECONDS"),
    )
    openai_image_timeout_seconds: int = Field(
        default=120,
        validation_alias=AliasChoices("OPENAI_IMAGE_TIMEOUT_SECONDS"),
    )
    openai_max_retry_attempts: int = Field(
        default=3,
        validation_alias=AliasChoices("OPENAI_MAX_RETRY_ATTEMPTS"),
    )
    openai_max_output_tokens: int = Field(
        default=1800,
        validation_alias=AliasChoices("OPENAI_MAX_OUTPUT_TOKENS"),
    )

    admin_bearer_token: SecretStr = Field(validation_alias=AliasChoices("ADMIN_BEARER_TOKEN"))
    allowed_cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=list,
        validation_alias=AliasChoices("ALLOWED_CORS_ORIGINS"),
    )
    admin_rate_limit_requests_per_minute: int = Field(
        default=20,
        validation_alias=AliasChoices("ADMIN_RATE_LIMIT_REQUESTS_PER_MINUTE"),
    )

    generation_lock_timeout_seconds: int = Field(
        default=1800,
        validation_alias=AliasChoices("GENERATION_LOCK_TIMEOUT_SECONDS"),
    )
    generation_max_retry_count: int = Field(
        default=3,
        validation_alias=AliasChoices("GENERATION_MAX_RETRY_COUNT"),
    )
    auto_publish_generated_recipes: bool = Field(
        default=False,
        validation_alias=AliasChoices("AUTO_PUBLISH_GENERATED_RECIPES"),
    )

    default_recipe_language_code: str = Field(
        default="ru-RU",
        validation_alias=AliasChoices("DEFAULT_RECIPE_LANGUAGE_CODE"),
    )
    default_cuisine_context: str = Field(
        default="modern home cooking",
        validation_alias=AliasChoices("DEFAULT_CUISINE_CONTEXT"),
    )
    default_dietary_context: str = Field(
        default="balanced",
        validation_alias=AliasChoices("DEFAULT_DIETARY_CONTEXT"),
    )
    default_excluded_ingredients: Annotated[list[str], NoDecode] = Field(
        default_factory=list,
        validation_alias=AliasChoices("DEFAULT_EXCLUDED_INGREDIENTS"),
    )
    default_image_style: str = Field(
        default="editorial food photography",
        validation_alias=AliasChoices("DEFAULT_IMAGE_STYLE"),
    )
    default_maximum_ingredients: int = Field(
        default=14,
        validation_alias=AliasChoices("DEFAULT_MAX_INGREDIENTS"),
    )
    default_maximum_steps: int = Field(
        default=8,
        validation_alias=AliasChoices("DEFAULT_MAX_STEPS"),
    )

    request_timeout_seconds: int = Field(
        default=15,
        validation_alias=AliasChoices("REQUEST_TIMEOUT_SECONDS"),
    )
    http_connect_timeout_seconds: int = Field(
        default=5,
        validation_alias=AliasChoices("HTTP_CONNECT_TIMEOUT_SECONDS"),
    )

    recipe_feed_page_size: int = 20
    image_output_size: str = "1024x1024"
    image_output_quality: str = "high"
    image_output_format: str = "png"

    @field_validator("allowed_cors_origins", mode="before")
    @classmethod
    def parse_allowed_cors_origins(cls, raw_value: object) -> list[str]:
        """Allow comma-separated CORS origins in environment variables."""

        if raw_value is None or raw_value == "":
            return []
        if isinstance(raw_value, list):
            return [str(item).strip() for item in raw_value if str(item).strip()]
        return [item.strip() for item in str(raw_value).split(",") if item.strip()]

    @field_validator("default_excluded_ingredients", mode="before")
    @classmethod
    def parse_default_excluded_ingredients(cls, raw_value: object) -> list[str]:
        """Allow comma-separated excluded ingredients in environment variables."""

        if raw_value is None or raw_value == "":
            return []
        if isinstance(raw_value, list):
            return [str(item).strip() for item in raw_value if str(item).strip()]
        return [item.strip() for item in str(raw_value).split(",") if item.strip()]

    @field_validator("app_environment")
    @classmethod
    def normalize_app_environment(cls, raw_value: str) -> str:
        """Normalize environment labels."""

        return raw_value.lower().strip()

    @field_validator("admin_bearer_token")
    @classmethod
    def validate_admin_bearer_token_strength(cls, raw_value: SecretStr) -> SecretStr:
        """Require a minimally strong admin token outside tests."""

        if len(raw_value.get_secret_value().strip()) < 24:
            raise ValueError("ADMIN_BEARER_TOKEN must be at least 24 characters long.")
        return raw_value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object."""

    return Settings()
