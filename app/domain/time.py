"""Time helpers centralised for repeatable UTC handling."""

from __future__ import annotations

from datetime import datetime, timezone


def get_current_utc_datetime() -> datetime:
    """Return the current timezone-aware UTC datetime."""

    return datetime.now(timezone.utc)


def normalize_to_hour_slot(target_datetime: datetime) -> datetime:
    """Normalize any datetime to the start of its UTC hour slot."""

    normalized_datetime = target_datetime.astimezone(timezone.utc)
    return normalized_datetime.replace(minute=0, second=0, microsecond=0)
