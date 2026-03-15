"""Request and job correlation helpers based on context variables."""

from __future__ import annotations

from uuid import uuid4

import structlog


def generate_request_id() -> str:
    """Generate a stable request identifier."""

    return str(uuid4())


def bind_context(
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
    job_id: str | None = None,
    admin_actor: str | None = None,
) -> None:
    """Bind request-scoped context to logs."""

    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        correlation_id=correlation_id,
        job_id=job_id,
        admin_actor=admin_actor,
    )


def clear_context() -> None:
    """Clear all bound context variables."""

    structlog.contextvars.clear_contextvars()
