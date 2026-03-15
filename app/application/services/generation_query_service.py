"""Read-only access to generation jobs."""

from __future__ import annotations

from uuid import UUID

from app.application.exceptions import NotFoundError
from app.application.ports.repositories import GenerationJobRepository
from app.domain.entities import GenerationJob


class GenerationQueryService:
    """Expose generation job state to admin callers."""

    def __init__(self, *, generation_job_repository: GenerationJobRepository) -> None:
        self._generation_job_repository = generation_job_repository

    def get_job_by_id(self, job_id: UUID) -> GenerationJob:
        """Return a generation job or raise a not-found error."""

        job = self._generation_job_repository.get_by_id(job_id)
        if job is None:
            raise NotFoundError(f"Generation job '{job_id}' was not found.")
        return job
