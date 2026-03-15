"""Health endpoint schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.api.schemas.examples import (
    HEALTH_COMPONENT_EXAMPLE,
    HEALTH_RESPONSE_EXAMPLE,
    PUBLIC_HEALTH_RESPONSE_EXAMPLE,
)


class HealthComponentResponse(BaseModel):
    """Per-component health status."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": HEALTH_COMPONENT_EXAMPLE},
    )

    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    """Top-level health response."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": HEALTH_RESPONSE_EXAMPLE},
    )

    status: str
    timestamp_utc: datetime
    components: dict[str, HealthComponentResponse]


class PublicHealthResponse(BaseModel):
    """Shallow public health response."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": PUBLIC_HEALTH_RESPONSE_EXAMPLE},
    )

    status: str
    timestamp_utc: datetime
