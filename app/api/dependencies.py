"""FastAPI dependency wiring."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.application.services.generation_query_service import GenerationQueryService
from app.application.services.recipe_publication_service import RecipePublicationService
from app.application.services.recipe_query_service import RecipeQueryService
from app.bootstrap import ApplicationContainer
from app.infrastructure.database.repositories.generation_job_repository import (
    SqlAlchemyGenerationJobRepository,
)
from app.infrastructure.database.repositories.recipe_repository import SqlAlchemyRecipeRepository
from app.observability.context import bind_context
from app.security.auth import AdminIdentity, require_admin_identity


def get_container(request: Request) -> ApplicationContainer:
    """Return the application container stored in app state."""

    return request.app.state.container


def get_database_session(
    container: ApplicationContainer = Depends(get_container),
) -> Generator[Session, None, None]:
    """Yield a request-scoped SQLAlchemy session."""

    session = container.session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_recipe_query_service(
    database_session: Session = Depends(get_database_session),
) -> RecipeQueryService:
    """Create the public recipe query service."""

    return RecipeQueryService(
        recipe_repository=SqlAlchemyRecipeRepository(session=database_session),
    )


def get_recipe_publication_service(
    database_session: Session = Depends(get_database_session),
) -> RecipePublicationService:
    """Create the recipe publication service."""

    return RecipePublicationService(
        recipe_repository=SqlAlchemyRecipeRepository(session=database_session),
        database_session=database_session,
    )


def get_generation_query_service(
    database_session: Session = Depends(get_database_session),
) -> GenerationQueryService:
    """Create the generation query service."""

    return GenerationQueryService(
        generation_job_repository=SqlAlchemyGenerationJobRepository(session=database_session),
    )


def get_generation_service(
    container: ApplicationContainer = Depends(get_container),
):
    """Create the main generation service."""

    return container.build_generation_service()


def get_health_service(container: ApplicationContainer = Depends(get_container)):
    """Create the health service."""

    return container.build_health_service()


def require_admin_access(
    request: Request,
    admin_identity: AdminIdentity = Depends(require_admin_identity),
    container: ApplicationContainer = Depends(get_container),
) -> AdminIdentity:
    """Authenticate and rate-limit admin endpoints."""

    container.admin_rate_limiter.enforce(request=request, admin_identity=admin_identity)
    bind_context(admin_actor=admin_identity.actor_id)
    return admin_identity
