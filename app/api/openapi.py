"""OpenAPI metadata helpers for the FastAPI application."""

from __future__ import annotations

from importlib.metadata import (
    PackageNotFoundError,
)
from importlib.metadata import (
    version as load_package_version,
)

OPENAPI_DESCRIPTION = (
    "Trusted backend API for scheduled AI recipe generation, publication workflows, "
    "and public recipe delivery.\n\n"
    "Use the `public` endpoints for client-safe recipe reads, the `admin` endpoints "
    "for operator-only controls, the `generation` endpoints for manual generation "
    "dispatch and job inspection, and the `health` endpoints for public liveness "
    "or authenticated readiness checks."
)

OPENAPI_TAGS = [
    {
        "name": "public",
        "description": "Public recipe endpoints that expose only published, client-safe content.",
    },
    {
        "name": "admin",
        "description": "Authenticated operator endpoints for publication and operational controls.",
    },
    {
        "name": "generation",
        "description": "Manual generation dispatch and generation job inspection endpoints.",
    },
    {
        "name": "health",
        "description": "Liveness and readiness endpoints for API and dependency checks.",
    },
]


def get_application_version() -> str:
    """Return the installed project version with a safe fallback."""

    try:
        return load_package_version("pech-da-lozhka-backend")
    except PackageNotFoundError:
        return "0.1.0"
