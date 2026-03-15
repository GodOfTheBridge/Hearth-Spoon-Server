"""Redis client factory."""

from __future__ import annotations

import redis

from app.config.settings import Settings


def build_redis_client(settings: Settings) -> redis.Redis:
    """Create a Redis client with predictable timeout settings."""

    return redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=settings.http_connect_timeout_seconds,
        socket_timeout=settings.request_timeout_seconds,
        health_check_interval=30,
    )
