"""Схемы эндпоинтов проверки состояния."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.examples import (
    HEALTH_COMPONENT_EXAMPLE,
    HEALTH_RESPONSE_EXAMPLE,
    PUBLIC_HEALTH_RESPONSE_EXAMPLE,
)


class HealthComponentResponse(BaseModel):
    """Статус отдельного компонента инфраструктуры."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": HEALTH_COMPONENT_EXAMPLE},
    )

    status: str = Field(description="Статус конкретного компонента.")
    detail: str | None = Field(
        default=None,
        description="Дополнительная диагностическая информация, если она доступна.",
    )


class HealthResponse(BaseModel):
    """Верхнеуровневый ответ о готовности сервиса."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": HEALTH_RESPONSE_EXAMPLE},
    )

    status: str = Field(description="Общий статус готовности сервиса.")
    timestamp_utc: datetime = Field(description="Время формирования ответа в UTC.")
    components: dict[str, HealthComponentResponse] = Field(
        description="Статусы отдельных зависимостей и компонентов."
    )


class PublicHealthResponse(BaseModel):
    """Укороченный публичный ответ о доступности сервиса."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": PUBLIC_HEALTH_RESPONSE_EXAMPLE},
    )

    status: str = Field(description="Публичный статус доступности сервиса.")
    timestamp_utc: datetime = Field(description="Время формирования ответа в UTC.")
