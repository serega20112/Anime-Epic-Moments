"""Abstract highlight dashboard cache interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class HighlightDashboardCacheInterface(ABC):
    """Interface for caching highlight dashboard data."""

    @abstractmethod
    async def get_dashboard(self, key: str) -> Any:
        """Get cached dashboard data.

        Args:
            key: Cache key.

        Returns:
            Any: Cached dashboard data or None.
        """

    @abstractmethod
    async def set_dashboard(self, key: str, data: Any, ttl_seconds: int | None = None) -> None:
        """Store dashboard data in cache.

        Args:
            key: Cache key.
            data: Dashboard data to cache.
            ttl_seconds: Optional TTL in seconds.
        """

    @abstractmethod
    async def invalidate(self, key: str | None = None) -> None:
        """Invalidate cached dashboard data.

        Args:
            key: Optional specific key to invalidate. If None, invalidates all.
        """
