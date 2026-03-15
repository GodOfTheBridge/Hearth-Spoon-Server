"""Redis-backed rate limiting for admin endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

import redis
import structlog
from fastapi import HTTPException, Request, status

from app.security.auth import AdminIdentity

logger = structlog.get_logger(__name__)


class AdminRateLimiter:
    """Apply a simple fixed-window rate limit to admin requests."""

    def __init__(self, *, redis_client: redis.Redis, requests_per_minute: int) -> None:
        self._redis_client = redis_client
        self._requests_per_minute = requests_per_minute

    def enforce(self, *, request: Request, admin_identity: AdminIdentity) -> None:
        """Raise HTTP 429 when the admin request exceeds the configured rate."""

        current_minute_bucket = datetime.now(UTC).strftime("%Y%m%d%H%M")
        rate_limit_key = (
            f"rate-limit:admin:{admin_identity.actor_id}:{request.url.path}:{current_minute_bucket}"
        )

        try:
            current_count = cast(int, self._redis_client.incr(rate_limit_key))
            if current_count == 1:
                self._redis_client.expire(rate_limit_key, 60)
        except redis.RedisError as error:
            logger.error("admin.rate_limit.redis_unavailable", error=str(error))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin rate limiting is temporarily unavailable.",
            ) from error

        if current_count > self._requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Admin rate limit exceeded.",
            )
