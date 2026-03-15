"""Admin authentication and coarse-grained authorization helpers."""

from __future__ import annotations

from hmac import compare_digest

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict

from app.application.exceptions import AuthenticationError, AuthorizationError
from app.config.settings import Settings, get_settings
from app.security.safety import build_hashed_safety_identifier

admin_bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="AdminBearerAuth",
    description=(
        "Bearer token for authenticated admin endpoints. "
        "Use a token configured through ADMIN_IDENTITIES or ADMIN_BEARER_TOKEN."
    ),
    bearerFormat="Opaque token",
)


class AdminIdentity(BaseModel):
    """Authenticated admin identity derived from configured operator tokens."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str
    actor_label: str
    roles: list[str]

    def has_read_access(self) -> bool:
        """Return whether this identity may access read-only admin endpoints."""

        return "read" in self.roles or "write" in self.roles

    def has_write_access(self) -> bool:
        """Return whether this identity may access mutating admin endpoints."""

        return "write" in self.roles


def require_admin_identity(
    credentials: HTTPAuthorizationCredentials | None = Security(admin_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> AdminIdentity:
    """Validate the presented bearer token against configured admin identities."""

    if credentials is None:
        raise AuthenticationError("Missing admin bearer token.")

    provided_token = credentials.credentials.strip()
    for configured_identity in settings.get_admin_configured_identities():
        expected_token = configured_identity.token.get_secret_value().strip()
        if not compare_digest(provided_token, expected_token):
            continue

        actor_id = build_hashed_safety_identifier(
            namespace="admin-actor",
            raw_identifier=configured_identity.actor_label,
        )
        return AdminIdentity(
            actor_id=actor_id,
            actor_label=configured_identity.actor_label,
            roles=configured_identity.roles,
        )

    raise AuthenticationError("Invalid admin bearer token.")


def require_admin_read_role(
    admin_identity: AdminIdentity = Depends(require_admin_identity),
) -> AdminIdentity:
    """Require an authenticated admin identity with read access."""

    if not admin_identity.has_read_access():
        raise AuthorizationError("Admin token does not have read access.")
    return admin_identity


def require_admin_write_role(
    admin_identity: AdminIdentity = Depends(require_admin_identity),
) -> AdminIdentity:
    """Require an authenticated admin identity with write access."""

    if not admin_identity.has_write_access():
        raise AuthorizationError("Admin token does not have write access.")
    return admin_identity
