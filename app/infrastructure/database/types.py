"""Shared SQLAlchemy types."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

JSON_VARIANT = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")
