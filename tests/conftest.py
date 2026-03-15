"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings
from app.infrastructure.database.base import Base
from app.infrastructure.database.session import create_database_engine, create_session_factory


@pytest.fixture(autouse=True)
def configured_test_environment(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Provide a fully configured environment for tests."""

    environment_values = {
        "APP_ENVIRONMENT": "test",
        "DATABASE_URL": "sqlite+pysqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/15",
        "S3_ENDPOINT_URL": "http://localhost:9000",
        "S3_REGION_NAME": "us-east-1",
        "S3_BUCKET_NAME": "test-bucket",
        "S3_ACCESS_KEY_ID": "test-access-key",
        "S3_SECRET_ACCESS_KEY": "test-secret-key",
        "S3_USE_SSL": "false",
        "S3_PUBLIC_BASE_URL": "https://cdn.example.test/test-bucket",
        "S3_PUBLIC_ENDPOINT_URL": "https://cdn.example.test",
        "OPENAI_API_KEY": "test-openai-key",
        "OPENAI_PROJECT_ID": "",
        "ADMIN_IDENTITIES": (
            "ops-read|test-read-token-which-is-long-enough|read;"
            "ops-write|test-write-token-which-is-long-enough|read,write"
        ),
        "ADMIN_BEARER_TOKEN": "test-admin-token-which-is-long-enough",
        "ALLOWED_CORS_ORIGINS": "http://localhost:3000",
    }

    for key, value in environment_values.items():
        monkeypatch.setenv(key, value)

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def sqlite_session_factory() -> sessionmaker[Session]:
    """Create an in-memory SQLite session factory for tests."""

    settings = get_settings()
    engine = create_database_engine(settings)
    Base.metadata.create_all(engine)
    return create_session_factory(engine)
