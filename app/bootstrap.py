"""Application bootstrap and dependency wiring."""

from __future__ import annotations

from dataclasses import dataclass

import redis
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.locking import DistributedLockManager
from app.application.services.generation_service import RecipeGenerationService
from app.application.services.health_service import HealthService
from app.application.services.image_prompt_builder import ImagePromptBuilder
from app.application.services.recipe_prompt_builder import RecipePromptBuilder
from app.config.settings import Settings, get_settings
from app.infrastructure.cache.redis import build_redis_client
from app.infrastructure.database.repositories.generation_job_repository import (
    SqlAlchemyGenerationJobRepository,
)
from app.infrastructure.database.repositories.generation_schedule_slot_repository import (
    SqlAlchemyGenerationScheduleSlotRepository,
)
from app.infrastructure.database.repositories.recipe_repository import SqlAlchemyRecipeRepository
from app.infrastructure.database.session import create_database_engine, create_session_factory
from app.infrastructure.locking.composite_lock import CompositeDistributedLockManager
from app.infrastructure.locking.postgres_lock import PostgresAdvisoryLockManager
from app.infrastructure.locking.redis_lock import RedisDistributedLockManager
from app.infrastructure.providers.openai.client import OpenAIClientWrapper
from app.infrastructure.providers.openai.recipe_image_generation_provider import (
    OpenAIRecipeImageGenerationProvider,
)
from app.infrastructure.providers.openai.recipe_text_generation_provider import (
    OpenAIRecipeTextGenerationProvider,
)
from app.infrastructure.storage.s3_storage import S3ObjectStorage
from app.security.rate_limiter import AdminRateLimiter


@dataclass(slots=True)
class ApplicationContainer:
    """A lightweight container for long-lived infrastructure objects."""

    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    redis_client: redis.Redis
    object_storage: S3ObjectStorage
    distributed_lock_manager: DistributedLockManager
    recipe_text_generation_provider: OpenAIRecipeTextGenerationProvider
    recipe_image_generation_provider: OpenAIRecipeImageGenerationProvider
    admin_rate_limiter: AdminRateLimiter

    def build_generation_service(self) -> RecipeGenerationService:
        """Build the main generation orchestration service."""

        return RecipeGenerationService(
            settings=self.settings,
            session_factory=self.session_factory,
            recipe_repository_factory=lambda session: SqlAlchemyRecipeRepository(session=session),
            generation_job_repository_factory=lambda session: SqlAlchemyGenerationJobRepository(
                session=session
            ),
            generation_schedule_slot_repository_factory=lambda session: (
                SqlAlchemyGenerationScheduleSlotRepository(session=session)
            ),
            recipe_text_generation_provider=self.recipe_text_generation_provider,
            recipe_image_generation_provider=self.recipe_image_generation_provider,
            object_storage=self.object_storage,
            distributed_lock_manager=self.distributed_lock_manager,
            recipe_prompt_builder=RecipePromptBuilder(),
            image_prompt_builder=ImagePromptBuilder(),
        )

    def build_health_service(self) -> HealthService:
        """Build the health service."""

        return HealthService(
            database_engine=self.engine,
            redis_client=self.redis_client,
            object_storage=self.object_storage,
        )

    def close(self) -> None:
        """Release long-lived resources."""

        self.redis_client.close()
        self.engine.dispose()


def build_application_container(settings: Settings | None = None) -> ApplicationContainer:
    """Create the application container."""

    resolved_settings = settings or get_settings()
    engine = create_database_engine(resolved_settings)
    session_factory = create_session_factory(engine)
    redis_client = build_redis_client(resolved_settings)
    object_storage = S3ObjectStorage(settings=resolved_settings)
    redis_lock_manager = RedisDistributedLockManager(redis_client=redis_client)
    distributed_lock_manager: DistributedLockManager = redis_lock_manager
    if engine.dialect.name == "postgresql":
        postgres_lock_manager = PostgresAdvisoryLockManager(database_engine=engine)
        distributed_lock_manager = CompositeDistributedLockManager(
            lock_managers=[redis_lock_manager, postgres_lock_manager]
        )
    openai_client_wrapper = OpenAIClientWrapper(settings=resolved_settings)
    recipe_text_generation_provider = OpenAIRecipeTextGenerationProvider(
        openai_client_wrapper=openai_client_wrapper
    )
    recipe_image_generation_provider = OpenAIRecipeImageGenerationProvider(
        openai_client_wrapper=openai_client_wrapper,
        model_name=resolved_settings.openai_image_model,
    )
    admin_rate_limiter = AdminRateLimiter(
        redis_client=redis_client,
        requests_per_minute=resolved_settings.admin_rate_limit_requests_per_minute,
    )

    return ApplicationContainer(
        settings=resolved_settings,
        engine=engine,
        session_factory=session_factory,
        redis_client=redis_client,
        object_storage=object_storage,
        distributed_lock_manager=distributed_lock_manager,
        recipe_text_generation_provider=recipe_text_generation_provider,
        recipe_image_generation_provider=recipe_image_generation_provider,
        admin_rate_limiter=admin_rate_limiter,
    )
