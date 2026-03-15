"""Concrete schedule slot repository implementation."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.ports.repositories import GenerationScheduleSlotRepository
from app.domain.entities import GenerationScheduleSlot
from app.domain.enums import GenerationSlotStatus, GenerationType
from app.domain.exceptions import NotFoundError
from app.infrastructure.database.mappers import map_generation_schedule_slot_model_to_domain
from app.infrastructure.database.models import GenerationScheduleSlotModel


class SqlAlchemyGenerationScheduleSlotRepository(GenerationScheduleSlotRepository):
    """SQLAlchemy-backed generation slot repository."""

    def __init__(self, *, session: Session) -> None:
        self._session = session

    def get_by_id(self, slot_id: UUID) -> GenerationScheduleSlot | None:
        """Return a slot by identifier."""

        slot_model = self._session.get(GenerationScheduleSlotModel, slot_id)
        if slot_model is None:
            return None
        return map_generation_schedule_slot_model_to_domain(slot_model)

    def get_or_create_slot(
        self,
        *,
        slot_time_utc: datetime,
        generation_type: GenerationType,
    ) -> GenerationScheduleSlot:
        """Return an existing slot or create a new one."""

        statement = select(GenerationScheduleSlotModel).where(
            GenerationScheduleSlotModel.slot_time_utc == slot_time_utc,
            GenerationScheduleSlotModel.generation_type == generation_type,
        )
        slot_model = self._session.execute(statement).scalars().first()
        if slot_model is None:
            slot_model = GenerationScheduleSlotModel(
                slot_time_utc=slot_time_utc,
                generation_type=generation_type,
            )
            self._session.add(slot_model)
            self._session.flush()
        return map_generation_schedule_slot_model_to_domain(slot_model)

    def update_slot_status(
        self,
        *,
        slot_id: UUID,
        status: GenerationSlotStatus,
        locked_at: datetime | None = None,
    ) -> GenerationScheduleSlot:
        """Update the slot status."""

        slot_model = self._session.get(GenerationScheduleSlotModel, slot_id)
        if slot_model is None:
            raise NotFoundError(f"Generation schedule slot '{slot_id}' was not found.")

        slot_model.status = status
        slot_model.locked_at = locked_at
        self._session.flush()
        return map_generation_schedule_slot_model_to_domain(slot_model)
