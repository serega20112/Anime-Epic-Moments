"""Redis cache and security state settings."""

from __future__ import annotations

import os


def redis_enabled() -> bool:
    """Return whether Redis is enabled.

    Returns:
        bool: True when REDIS_ENABLED is enabled.
    """
    return os.getenv("REDIS_ENABLED", "1") == "1"


def redis_required() -> bool:
    """Return whether Redis is required for the application to start.

    Returns:
        bool: True when REDIS_REQUIRED is enabled.
    """
    return os.getenv("REDIS_REQUIRED", "0") == "1"


def redis_url() -> str | None:
    """Return the Redis connection URL.

    Returns:
        str | None: Redis URL or None when Redis is disabled.
    """
    if not redis_enabled():
        return None
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")