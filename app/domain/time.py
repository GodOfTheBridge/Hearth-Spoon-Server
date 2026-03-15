"""Time helpers centralised for repeatable UTC handling."""

from __future__ import annotations

from datetime import UTC, datetime


def get_current_utc_datetime() -> datetime:
    """Return the current timezone-aware UTC datetime."""

    return datetime.now(UTC)


def normalize_to_hour_slot(target_datetime: datetime) -> datetime:
    """Normalize any datetime to the start of its UTC hour slot."""

    normalized_datetime = target_datetime.astimezone(UTC)
    return normalized_datetime.replace(minute=0, second=0, microsecond=0)
