"""Публичный эндпоинт проверки доступности."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_health_service
from app.api.schemas.health import PublicHealthResponse

router = APIRouter(tags=["Состояние сервиса"])


@router.get(
    "/health",
    response_model=PublicHealthResponse,
    summary="Проверить доступность API",
    description=(
        "Возвращает укороченный публичный статус сервиса "
        "без деталей внутренних зависимостей."
    ),
    response_description="Публичный статус доступности API.",
)
def get_health(health_service=Depends(get_health_service)) -> JSONResponse:
    """Возвращает укороченный публичный статус доступности сервиса."""

    health_payload = health_service.check_public_liveness()
    response_model = PublicHealthResponse.model_validate(
        {
            "status": health_payload["status"],
            "timestamp_utc": health_payload["timestamp_utc"],
        }
    )
    response_status_code = (
        status.HTTP_200_OK
        if response_model.status == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(
        status_code=response_status_code,
        content=response_model.model_dump(mode="json"),
    )
