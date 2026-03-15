"""Custom exceptions used to keep error handling explicit across layers."""

from __future__ import annotations


class DomainError(Exception):
    """Base exception for all domain and application errors."""


class NotFoundError(DomainError):
    """Raised when a requested resource does not exist."""


class AuthenticationError(DomainError):
    """Raised when authentication fails."""


class AuthorizationError(DomainError):
    """Raised when an authenticated principal is not allowed to act."""


class ConfigurationError(DomainError):
    """Raised when runtime configuration is incomplete or invalid."""


class ValidationFailureError(DomainError):
    """Raised when strict input validation fails."""


class ExternalProviderError(DomainError):
    """Raised when an external provider returns an unrecoverable failure."""


class StructuredOutputValidationError(ValidationFailureError):
    """Raised when the provider returns malformed structured output."""


class StorageOperationError(DomainError):
    """Raised when object storage operations fail."""


class DatabaseOperationError(DomainError):
    """Raised when a database write or query fails."""


class IdempotencyConflictError(DomainError):
    """Raised when the same logical generation is already in progress."""


class RetryExhaustedError(DomainError):
    """Raised when safe retry attempts have been exhausted."""
