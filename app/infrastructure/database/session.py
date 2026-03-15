"""Database engine and session factory."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.settings import Settings


def create_database_engine(settings: Settings) -> Engine:
    """Create the SQLAlchemy engine."""

    engine_options: dict[str, object] = {
        "future": True,
        "pool_pre_ping": True,
    }
    if settings.database_url.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}
        engine_options["poolclass"] = StaticPool

    return create_engine(settings.database_url, **engine_options)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create the SQLAlchemy session factory."""

    return sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
