"""Public health endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_health_service
from app.api.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health(health_service=Depends(get_health_service)) -> JSONResponse:
    """Return health information for probes and operators."""

    health_payload = health_service.check()
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
