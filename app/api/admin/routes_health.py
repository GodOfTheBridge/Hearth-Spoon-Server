"""Admin health endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_health_service
from app.api.schemas.health import HealthResponse
from app.security.auth import require_admin_identity

router = APIRouter(prefix="/admin/health", tags=["admin-health"])


@router.get("/readiness", response_model=HealthResponse)
def get_readiness(
    _admin_identity=Depends(require_admin_identity),
    health_service=Depends(get_health_service),
) -> JSONResponse:
    """Return detailed dependency readiness for authenticated operators."""

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
