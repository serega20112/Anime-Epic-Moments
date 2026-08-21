"""Abstract recommendation cache interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RecommendationCacheInterface(ABC):
    """Interface for caching recommendation data."""

    @abstractmethod
    async def get(self, user_id: int) -> Any:
        """Get cached recommendations for a user.

        Args:
            user_id: The user identifier.

        Returns:
            Any: Cached recommendations or None.
        """

    @abstractmethod
    async def set(self, user_id: int, data: Any, ttl_seconds: int | None = None) -> None:
        """Store recommendations in cache.

        Args:
            user_id: The user identifier.
            data: Recommendation data to cache.
            ttl_seconds: Optional TTL in seconds.
        """

    @abstractmethod
    async def invalidate(self, user_id: int) -> None:
        """Invalidate cached recommendations for a user.

        Args:
            user_id: The user identifier.
        """
