"""Shared API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ApiErrorResponse(BaseModel):
    """Standardized API error payload."""

    model_config = ConfigDict(extra="forbid")

    detail: str
    request_id: str | None = None
