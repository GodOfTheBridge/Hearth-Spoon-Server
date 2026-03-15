"""Admin generation endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import get_generation_query_service, get_generation_service, require_admin_access
from app.api.schemas.generation import (
    GenerationJobResponse,
    RunGenerationNowRequest,
    RunGenerationNowResponse,
)
from app.security.auth import AdminIdentity

router = APIRouter(prefix="/admin/generations", tags=["admin-generations"])


@router.post("/run-now", response_model=RunGenerationNowResponse)
def run_generation_now(
    request_payload: RunGenerationNowRequest | None = None,
    admin_identity: AdminIdentity = Depends(require_admin_access),
    generation_service=Depends(get_generation_service),
) -> RunGenerationNowResponse:
    """Trigger generation immediately for the current or provided slot."""

    if request_payload and request_payload.slot_time_utc is not None:
        result = generation_service.run_for_slot(
            slot_time_utc=request_payload.slot_time_utc,
            requested_by=f"admin:{admin_identity.actor_id}",
        )
    else:
        result = generation_service.run_hourly_generation(
            requested_by=f"admin:{admin_identity.actor_id}",
        )
    return RunGenerationNowResponse.from_result(result)


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
