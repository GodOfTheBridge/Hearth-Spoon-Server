"""Generation-related API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.application.models import GenerationExecutionResult
from app.domain.entities import GenerationJob


class RunGenerationNowRequest(BaseModel):
    """Optional manual generation request payload."""

    model_config = ConfigDict(extra="forbid")

    slot_time_utc: datetime | None = None


class GenerationJobResponse(BaseModel):
    """Serialized generation job response."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    job_type: str
    schedule_slot: datetime
    idempotency_key: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    retry_count: int
    created_at: datetime

    @classmethod
    def from_domain(cls, generation_job: GenerationJob) -> GenerationJobResponse:
        """Build a response from the domain entity."""

        return cls(
            id=generation_job.id,
            job_type=generation_job.job_type,
            schedule_slot=generation_job.schedule_slot,
            idempotency_key=generation_job.idempotency_key,
            status=generation_job.status,
            started_at=generation_job.started_at,
            finished_at=generation_job.finished_at,
            error_message=generation_job.error_message,
            retry_count=generation_job.retry_count,
            created_at=generation_job.created_at,
        )


class RunGenerationNowResponse(BaseModel):
    """Response returned from the manual generation endpoint."""

    model_config = ConfigDict(extra="forbid")

    job: GenerationJobResponse
    recipe_id: UUID | None = None
    was_created: bool
    message: str

    @classmethod
    def from_result(cls, result: GenerationExecutionResult) -> RunGenerationNowResponse:
        """Build a response from the application result."""

        return cls(
            job=GenerationJobResponse.from_domain(result.job),
            recipe_id=result.recipe.id if result.recipe else None,
            was_created=result.was_created,
            message=result.message,
        )
