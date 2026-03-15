"""Admin generation endpoints."""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse

from app.api.dependencies import (
    get_generation_query_service,
    get_generation_service,
    require_admin_access,
)
from app.api.schemas.generation import (
    GenerationJobResponse,
    RunGenerationNowRequest,
    RunGenerationNowResponse,
)
from app.application.exceptions import IdempotencyConflictError
from app.domain.time import get_current_utc_datetime, normalize_to_hour_slot
from app.security.auth import AdminIdentity

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/admin/generations", tags=["admin-generations"])


def _run_generation_in_background(*, generation_service, slot_time_utc, requested_by: str) -> None:
    """Execute manual generation in the background and log failures clearly."""

    try:
        generation_service.run_for_slot(
            slot_time_utc=slot_time_utc,
            requested_by=requested_by,
        )
    except IdempotencyConflictError:
        logger.info(
            "admin.generation.background_skipped",
            slot_time_utc=slot_time_utc.isoformat(),
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "admin.generation.background_failed",
            slot_time_utc=slot_time_utc.isoformat(),
        )


@router.post(
    "/run-now",
    response_model=RunGenerationNowResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def run_generation_now(
    background_tasks: BackgroundTasks,
    request_payload: RunGenerationNowRequest | None = None,
    admin_identity: AdminIdentity = Depends(require_admin_access),
    generation_service=Depends(get_generation_service),
) -> JSONResponse:
    """Trigger generation immediately for the current or provided slot."""

    requested_by = f"admin:{admin_identity.actor_id}"
    if request_payload and request_payload.slot_time_utc is not None:
        result = generation_service.prepare_background_generation(
            slot_time_utc=request_payload.slot_time_utc,
            requested_by=requested_by,
        )
    else:
        result = generation_service.prepare_background_generation(
            slot_time_utc=normalize_to_hour_slot(get_current_utc_datetime()),
            requested_by=requested_by,
        )
    if result.was_enqueued:
        background_tasks.add_task(
            _run_generation_in_background,
            generation_service=generation_service,
            slot_time_utc=result.slot_time_utc,
            requested_by=requested_by,
        )

    response_model = RunGenerationNowResponse.from_result(result)
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=response_model.model_dump(mode="json"),
        background=background_tasks,
    )


@router.get("/{job_id}", response_model=GenerationJobResponse)
def get_generation_job(
    job_id: UUID,
    admin_identity: AdminIdentity = Depends(require_admin_access),
    generation_query_service=Depends(get_generation_query_service),
) -> GenerationJobResponse:
    """Return the status of a generation job."""

    _ = admin_identity
    generation_job = generation_query_service.get_job_by_id(job_id)
    return GenerationJobResponse.from_domain(generation_job)
