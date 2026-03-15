"""FastAPI middleware for request and correlation identifiers."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.observability.context import bind_context, clear_context, generate_request_id

REQUEST_ID_HEADER_NAME = "X-Request-Id"
CORRELATION_ID_HEADER_NAME = "X-Correlation-Id"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach request-level identifiers to logs and responses."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER_NAME, generate_request_id())
        correlation_id = request.headers.get(CORRELATION_ID_HEADER_NAME, request_id)

        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        bind_context(request_id=request_id, correlation_id=correlation_id)
        try:
            response = await call_next(request)
        finally:
            clear_context()

        response.headers[REQUEST_ID_HEADER_NAME] = request_id
        response.headers[CORRELATION_ID_HEADER_NAME] = correlation_id
        return response
