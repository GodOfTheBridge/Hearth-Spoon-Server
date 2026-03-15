"""Top-level API router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.admin.routes_generations import router as admin_generations_router
from app.api.admin.routes_health import router as admin_health_router
from app.api.admin.routes_recipes import router as admin_recipes_router
from app.api.public.routes_health import router as health_router
from app.api.public.routes_recipes import router as public_recipes_router


def build_api_router() -> APIRouter:
    """Build the versioned API router."""

    api_router = APIRouter(prefix="/api/v1")
    api_router.include_router(health_router)
    api_router.include_router(public_recipes_router)
    api_router.include_router(admin_health_router)
    api_router.include_router(admin_generations_router)
    api_router.include_router(admin_recipes_router)
    return api_router
