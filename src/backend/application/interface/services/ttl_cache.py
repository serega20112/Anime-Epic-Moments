"""Abstract TTL cache interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TTLCacheInterface(ABC):
    """Interface for TTL-based key-value caching."""

    @abstractmethod
    async def get(self, key: str) -> Any:
        """Get a value by key.

        Args:
            key: Cache key.

        Returns:
            Any: Cached value or None.
        """

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store a value with optional TTL.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl_seconds: Optional TTL in seconds.
        """

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a value by key.

        Args:
            key: Cache key.
        """

    @abstractmethod
    async def close(self) -> None:
        """Close cache resources."""
