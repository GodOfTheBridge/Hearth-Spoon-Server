"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from copy import deepcopy

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html

from app.api.errors import register_exception_handlers
from app.api.openapi import (
    DEFAULT_OPENAPI_LANGUAGE,
    OPENAPI_DESCRIPTION,
    OPENAPI_LANGUAGE_LABELS,
    OPENAPI_TAGS,
    get_application_version,
    localize_generated_openapi_terms,
    normalize_openapi_language,
    translate_openapi_texts_in_place,
)
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
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
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

    original_openapi = application.openapi
    localized_openapi_schemas: dict[str, dict[str, object]] = {}

    def get_openapi_document_url(language: str) -> str:
        normalized_language = normalize_openapi_language(language)
        return f"/openapi.{normalized_language}.json"

    def get_localized_openapi_schema(language: str) -> dict[str, object]:
        normalized_language = normalize_openapi_language(language)
        cached_schema = localized_openapi_schemas.get(normalized_language)
        if cached_schema is not None:
            return cached_schema

        base_schema = localized_openapi_schemas.get(DEFAULT_OPENAPI_LANGUAGE)
        if base_schema is None:
            base_schema = original_openapi()
            localize_generated_openapi_terms(base_schema)
            localized_openapi_schemas[DEFAULT_OPENAPI_LANGUAGE] = base_schema

        if normalized_language == DEFAULT_OPENAPI_LANGUAGE:
            return base_schema

        localized_schema = deepcopy(base_schema)
        translate_openapi_texts_in_place(localized_schema, language=normalized_language)
        localized_openapi_schemas[normalized_language] = localized_schema
        return localized_schema

    def custom_openapi():
        return get_localized_openapi_schema(DEFAULT_OPENAPI_LANGUAGE)

    application.openapi = custom_openapi  # type: ignore[method-assign]

    if is_docs_enabled:
        swagger_ui_parameters = dict(application.swagger_ui_parameters or {})
        swagger_ui_parameters["layout"] = "StandaloneLayout"
        swagger_ui_parameters["urls"] = [
            {
                "url": get_openapi_document_url(DEFAULT_OPENAPI_LANGUAGE),
                "name": OPENAPI_LANGUAGE_LABELS[DEFAULT_OPENAPI_LANGUAGE],
            },
            {
                "url": get_openapi_document_url("en"),
                "name": OPENAPI_LANGUAGE_LABELS["en"],
            },
        ]
        swagger_ui_parameters["urls.primaryName"] = OPENAPI_LANGUAGE_LABELS[
            DEFAULT_OPENAPI_LANGUAGE
        ]

        @application.get("/openapi.json", include_in_schema=False)
        def get_openapi_json(
            lang: str = Query(default=DEFAULT_OPENAPI_LANGUAGE),
        ) -> dict[str, object]:
            return get_localized_openapi_schema(lang)

        @application.get("/openapi.ru.json", include_in_schema=False)
        def get_openapi_ru_json() -> dict[str, object]:
            return get_localized_openapi_schema(DEFAULT_OPENAPI_LANGUAGE)

        @application.get("/openapi.en.json", include_in_schema=False)
        def get_openapi_en_json() -> dict[str, object]:
            return get_localized_openapi_schema("en")

        @application.get("/docs", include_in_schema=False)
        def get_swagger_ui() -> object:
            return get_swagger_ui_html(
                openapi_url=get_openapi_document_url(DEFAULT_OPENAPI_LANGUAGE),
                title=f"{application.title} - Swagger UI",
                swagger_ui_parameters=swagger_ui_parameters,
            )

        @application.get("/redoc", include_in_schema=False)
        def get_redoc(
            lang: str = Query(default=DEFAULT_OPENAPI_LANGUAGE),
        ) -> object:
            return get_redoc_html(
                openapi_url=get_openapi_document_url(lang),
                title=f"{application.title} - ReDoc",
            )

    return application
