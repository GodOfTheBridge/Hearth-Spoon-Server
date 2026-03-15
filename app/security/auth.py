"""Simple bearer-token based admin authentication."""

from __future__ import annotations

from hmac import compare_digest

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict

from app.application.exceptions import AuthenticationError
from app.config.settings import Settings, get_settings
from app.security.safety import build_hashed_safety_identifier

http_bearer_scheme = HTTPBearer(auto_error=False)


class AdminIdentity(BaseModel):
    """Admin identity derived from the configured bearer token."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str


def require_admin_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> AdminIdentity:
    """Validate the admin bearer token using constant-time comparison."""

    if credentials is None:
        raise AuthenticationError("Missing admin bearer token.")

    provided_token = credentials.credentials.strip()
    expected_token = settings.admin_bearer_token.get_secret_value().strip()

    if not compare_digest(provided_token, expected_token):
        raise AuthenticationError("Invalid admin bearer token.")

    actor_id = build_hashed_safety_identifier(
        namespace="admin-actor",
        raw_identifier=provided_token,
    )
    return AdminIdentity(actor_id=actor_id)
