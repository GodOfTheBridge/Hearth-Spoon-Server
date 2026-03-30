"""Общие API-схемы."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.api.schemas.examples import API_ERROR_EXAMPLE


class ApiErrorResponse(BaseModel):
    """Стандартизированная схема ошибки API."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": API_ERROR_EXAMPLE})

    detail: str
    request_id: str | None = None
