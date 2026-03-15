"""Concrete generation job repository implementation."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.application.ports.repositories import GenerationJobRepository
from app.domain.entities import GenerationJob
from app.domain.enums import GenerationJobStatus, GenerationJobType
from app.domain.exceptions import NotFoundError
from app.infrastructure.database.mappers import map_generation_job_model_to_domain
from app.infrastructure.database.models import GenerationJobModel


class SqlAlchemyGenerationJobRepository(GenerationJobRepository):
    """SQLAlchemy-backed generation job repository."""

    def __init__(self, *, session: Session) -> None:
        self._session = session

    def get_by_id(self, job_id: UUID) -> GenerationJob | None:
        """Return a job by identifier."""

        statement = (
            select(GenerationJobModel)
            .options(joinedload(GenerationJobModel.schedule_slot))
            .where(GenerationJobModel.id == job_id)
        )
        job_model = self._session.execute(statement).unique().scalars().first()
        return map_generation_job_model_to_domain(job_model) if job_model else None

    def get_by_idempotency_key(self, idempotency_key: str) -> GenerationJob | None:
        """Return a job by idempotency key."""

        statement = (
            select(GenerationJobModel)
            .options(joinedload(GenerationJobModel.schedule_slot))
            .where(GenerationJobModel.idempotency_key == idempotency_key)
        )
        job_model = self._session.execute(statement).unique().scalars().first()
        return map_generation_job_model_to_domain(job_model) if job_model else None

    def get_latest_by_slot(self, slot_id: UUID) -> GenerationJob | None:
        """Return the latest job for a slot."""

        statement = (
            select(GenerationJobModel)
            .options(joinedload(GenerationJobModel.schedule_slot))
            .where(GenerationJobModel.schedule_slot_id == slot_id)
            .order_by(GenerationJobModel.created_at.desc())
            .limit(1)
        )
        job_model = self._session.execute(statement).unique().scalars().first()
        return map_generation_job_model_to_domain(job_model) if job_model else None

    def create_or_get_job(
        self,
        *,
        job_type: GenerationJobType,
        schedule_slot_id: UUID,
        idempotency_key: str,
        provider_request_metadata: dict[str, object],
    ) -> GenerationJob:
        """Create a job or return the existing row for the same idempotency key."""

        statement = (
            select(GenerationJobModel)
            .options(joinedload(GenerationJobModel.schedule_slot))
            .where(GenerationJobModel.idempotency_key == idempotency_key)
        )
        existing_job_model = self._session.execute(statement).unique().scalars().first()
        if existing_job_model is not None:
            return map_generation_job_model_to_domain(existing_job_model)

        job_model = GenerationJobModel(
            job_type=job_type,
            schedule_slot_id=schedule_slot_id,
            idempotency_key=idempotency_key,
            provider_request_metadata=provider_request_metadata,
        )
        self._session.add(job_model)
        self._session.flush()
        reloaded_statement = (
            select(GenerationJobModel)
            .options(joinedload(GenerationJobModel.schedule_slot))
            .where(GenerationJobModel.id == job_model.id)
        )
        reloaded_job_model = self._session.execute(reloaded_statement).unique().scalars().one()
        return map_generation_job_model_to_domain(reloaded_job_model)

    def update_job_status(
        self,
        *,
        job_id: UUID,
        status: GenerationJobStatus,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        error_message: str | None = None,
        retry_count: int | None = None,
        provider_request_metadata: dict[str, object] | None = None,
        provider_response_metadata: dict[str, object] | None = None,
    ) -> GenerationJob:
        """Update job state and metadata."""

        job_model = self._session.get(GenerationJobModel, job_id)
        if job_model is None:
            raise NotFoundError(f"Generation job '{job_id}' was not found.")

        job_model.status = status
        job_model.started_at = started_at
        job_model.finished_at = finished_at
        job_model.error_message = error_message
        if retry_count is not None:
            job_model.retry_count = retry_count
        if provider_request_metadata is not None:
            job_model.provider_request_metadata = provider_request_metadata
        if provider_response_metadata is not None:
            job_model.provider_response_metadata = provider_response_metadata

        self._session.flush()
        reloaded_statement = (
            select(GenerationJobModel)
            .options(joinedload(GenerationJobModel.schedule_slot))
            .where(GenerationJobModel.id == job_model.id)
        )
        reloaded_job_model = self._session.execute(reloaded_statement).unique().scalars().one()
        return map_generation_job_model_to_domain(reloaded_job_model)
