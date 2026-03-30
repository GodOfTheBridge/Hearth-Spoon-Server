"""Административные эндпоинты проверки состояния."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_health_service, require_admin_read_access
from app.api.schemas.health import HealthResponse

router = APIRouter(prefix="/admin/health", tags=["Администрирование", "Состояние сервиса"])


@router.get(
    "/readiness",
    response_model=HealthResponse,
    summary="Проверить готовность зависимостей",
    description=(
        "Возвращает детальный статус внутренних зависимостей "
        "для авторизованного администратора."
    ),
    response_description="Статус готовности зависимостей.",
)
def get_readiness(
    _admin_identity=Depends(require_admin_read_access),
    health_service=Depends(get_health_service),
) -> JSONResponse:
    """Возвращает детальный статус готовности внутренних зависимостей."""

    health_payload = health_service.check_readiness()
    response_model = HealthResponse.model_validate(health_payload)
    response_status_code = (
        status.HTTP_200_OK
        if response_model.status == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(
        status_code=response_status_code,
        content=response_model.model_dump(mode="json"),
    )
