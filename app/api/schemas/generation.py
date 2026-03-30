"""API-схемы, связанные с генерацией."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.schemas.examples import (
    GENERATION_JOB_EXAMPLE,
    RUN_GENERATION_NOW_REQUEST_EXAMPLE,
    RUN_GENERATION_NOW_RESPONSE_EXAMPLE,
)
from app.application.models import GenerationDispatchResult
from app.domain.entities import GenerationJob


class RunGenerationNowRequest(BaseModel):
    """Необязательное тело запроса для ручного запуска генерации."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": RUN_GENERATION_NOW_REQUEST_EXAMPLE},
    )

    slot_time_utc: datetime | None = Field(
        default=None,
        description=(
            "UTC-время часового слота, для которого нужно запустить генерацию. "
            "Если не указано, используется текущий UTC-час."
        ),
    )

    @field_validator("slot_time_utc")
    @classmethod
    def validate_timezone_aware_slot_time(cls, raw_value: datetime | None) -> datetime | None:
        """Reject naive datetimes so slot normalization is explicit and deterministic."""

        if raw_value is None:
            return None
        if raw_value.tzinfo is None:
            raise ValueError("slot_time_utc must be timezone-aware.")
        return raw_value


class GenerationJobResponse(BaseModel):
    """Сериализованный ответ со статусом задания генерации."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": GENERATION_JOB_EXAMPLE})

    id: UUID = Field(description="Идентификатор задания генерации.")
    job_type: str = Field(description="Тип задания генерации.")
    schedule_slot: datetime = Field(
        description="UTC-время часового слота, к которому относится задание."
    )
    idempotency_key: str = Field(
        description="Идемпотентный ключ, защищающий от повторного запуска."
    )
    status: str = Field(description="Текущее состояние задания генерации.")
    started_at: datetime | None = Field(
        default=None,
        description="Время начала выполнения задания в UTC.",
    )
    finished_at: datetime | None = Field(
        default=None,
        description="Время завершения задания в UTC.",
    )
    error_message: str | None = Field(
        default=None,
        description="Текст ошибки, если задание завершилось неуспешно.",
    )
    retry_count: int = Field(description="Количество повторных попыток выполнения.")
    created_at: datetime = Field(description="Время создания задания в UTC.")

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
    """Ответ эндпоинта ручного запуска генерации."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": RUN_GENERATION_NOW_RESPONSE_EXAMPLE},
    )

    slot_time_utc: datetime = Field(
        description="UTC-время часового слота, для которого обработан запрос."
    )
    job: GenerationJobResponse = Field(description="Текущее состояние задания генерации.")
    recipe_id: UUID | None = Field(
        default=None,
        description="Идентификатор рецепта, если он уже был создан.",
    )
    was_enqueued: bool = Field(
        description="Признак того, что выполнение было поставлено в фоновую очередь."
    )
    message: str = Field(description="Человекочитаемое пояснение результата постановки задания.")

    @classmethod
    def from_result(cls, result: GenerationDispatchResult) -> RunGenerationNowResponse:
        """Build a response from the application dispatch result."""

        return cls(
            slot_time_utc=result.slot_time_utc,
            job=GenerationJobResponse.from_domain(result.job),
            recipe_id=result.recipe.id if result.recipe else None,
            was_enqueued=result.was_enqueued,
            message=result.message,
        )
