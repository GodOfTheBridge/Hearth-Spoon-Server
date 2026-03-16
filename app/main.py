"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.openapi import OPENAPI_DESCRIPTION, OPENAPI_TAGS, get_application_version
from app.api.router import build_api_router
from app.bootstrap import build_application_container
from app.config.settings import get_settings
from app.observability.logging import configure_logging
from app.observability.middleware import RequestContextMiddleware


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Create and release long-lived resources."""

    settings = get_settings()
    configure_logging(settings)
    container = build_application_container(settings)
    application.state.container = container
    try:
        yield
    finally:
        container.close()


def create_app() -> FastAPI:
    """Create the configured FastAPI application."""

    settings = get_settings()
    is_docs_enabled = settings.app_debug or settings.app_environment == "development"
    application = FastAPI(
        title=settings.app_name,
        description=OPENAPI_DESCRIPTION,
        version=get_application_version(),
        debug=settings.app_debug,
        lifespan=lifespan,
        docs_url="/docs" if is_docs_enabled else None,
        redoc_url="/redoc" if is_docs_enabled else None,
        openapi_url="/openapi.json" if is_docs_enabled else None,
        openapi_tags=OPENAPI_TAGS,
        swagger_ui_parameters={
            "displayRequestDuration": True,
            "persistAuthorization": settings.app_environment == "development",
        },
    )

    application.add_middleware(RequestContextMiddleware)
    if settings.allowed_cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type", "X-Request-Id", "X-Correlation-Id"],
        )

    application.include_router(build_api_router())
    register_exception_handlers(application)
    return application
