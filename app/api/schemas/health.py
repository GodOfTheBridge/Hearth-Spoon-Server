"""Health endpoint schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HealthComponentResponse(BaseModel):
    """Per-component health status."""

    model_config = ConfigDict(extra="forbid")

    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    """Top-level health response."""

    model_config = ConfigDict(extra="forbid")

    status: str
    timestamp_utc: datetime
    components: dict[str, HealthComponentResponse]
