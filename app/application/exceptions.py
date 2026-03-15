"""Application-level aliases for domain exceptions."""

from __future__ import annotations

from app.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DatabaseOperationError,
    ExternalProviderError,
    IdempotencyConflictError,
    NotFoundError,
    RetryExhaustedError,
    StorageOperationError,
    StructuredOutputValidationError,
    ValidationFailureError,
)

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "ConfigurationError",
    "DatabaseOperationError",
    "ExternalProviderError",
    "IdempotencyConflictError",
    "NotFoundError",
    "RetryExhaustedError",
    "StorageOperationError",
    "StructuredOutputValidationError",
    "ValidationFailureError",
]
