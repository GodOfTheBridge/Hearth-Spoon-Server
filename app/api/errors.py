"""HTTP exception handlers."""

from __future__ import annotations

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.api.schemas.common import ApiErrorResponse
from app.application.exceptions import (
    AuthenticationError,
    DatabaseOperationError,
    ExternalProviderError,
    IdempotencyConflictError,
    NotFoundError,
    RetryExhaustedError,
    StorageOperationError,
    StructuredOutputValidationError,
    ValidationFailureError,
)

logger = structlog.get_logger(__name__)


def _build_error_response(
    *,
    request: Request,
    detail: str,
    status_code: int,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    payload = ApiErrorResponse(detail=detail, request_id=request_id)
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def register_exception_handlers(application: FastAPI) -> None:
    """Register all application exception handlers."""

    @application.exception_handler(AuthenticationError)
    async def handle_authentication_error(
        request: Request, exception: AuthenticationError
    ) -> JSONResponse:
        return _build_error_response(
            request=request,
            detail=str(exception),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    @application.exception_handler(NotFoundError)
    async def handle_not_found_error(request: Request, exception: NotFoundError) -> JSONResponse:
        return _build_error_response(
            request=request,
            detail=str(exception),
            status_code=status.HTTP_404_NOT_FOUND,
        )

    @application.exception_handler(IdempotencyConflictError)
    async def handle_idempotency_conflict_error(
        request: Request, exception: IdempotencyConflictError
    ) -> JSONResponse:
        return _build_error_response(
            request=request,
            detail=str(exception),
            status_code=status.HTTP_409_CONFLICT,
        )

    @application.exception_handler(RetryExhaustedError)
    async def handle_retry_exhausted_error(
        request: Request, exception: RetryExhaustedError
    ) -> JSONResponse:
        return _build_error_response(
            request=request,
            detail=str(exception),
            status_code=status.HTTP_409_CONFLICT,
        )

    @application.exception_handler(StructuredOutputValidationError)
    @application.exception_handler(ValidationFailureError)
    async def handle_validation_error(
        request: Request, exception: ValidationFailureError
    ) -> JSONResponse:
        return _build_error_response(
            request=request,
            detail=str(exception),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @application.exception_handler(ExternalProviderError)
    @application.exception_handler(StorageOperationError)
    async def handle_provider_error(
        request: Request, exception: Exception
    ) -> JSONResponse:
        return _build_error_response(
            request=request,
            detail=str(exception),
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    @application.exception_handler(DatabaseOperationError)
    async def handle_database_error(
        request: Request, exception: DatabaseOperationError
    ) -> JSONResponse:
        return _build_error_response(
            request=request,
            detail=str(exception),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @application.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exception: HTTPException) -> JSONResponse:
        return _build_error_response(
            request=request,
            detail=str(exception.detail),
            status_code=exception.status_code,
        )

    @application.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exception: Exception) -> JSONResponse:
        logger.exception("http.unhandled_exception", error_type=type(exception).__name__)
        return _build_error_response(
            request=request,
            detail="Internal server error.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
