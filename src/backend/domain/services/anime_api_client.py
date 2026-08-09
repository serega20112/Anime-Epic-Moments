"""Abstract anime API client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AnimeApiClientInterface(ABC):
    """Interface for external anime data API clients."""

    @abstractmethod
    async def get_by_id(self, anime_id: int) -> Any:
        """Get anime data by id.

        Args:
            anime_id: The anime identifier.

        Returns:
            Any: Anime data object or None.
        """

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[Any]:
        """Search anime by text query.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            list[Any]: List of anime data objects.
        """

    @abstractmethod
    async def autocomplete(self, prefix: str, limit: int = 8) -> list[Any]:
        """Autocomplete anime titles by prefix.

        Args:
            prefix: Title prefix to search.
            limit: Maximum number of results.

        Returns:
            list[Any]: List of anime data objects.
        """

    @abstractmethod
    async def get_season_popular(self, limit: int = 12) -> list[Any]:
        """Get popular anime for the current season.

        Args:
            limit: Maximum number of results.

        Returns:
            list[Any]: List of anime data objects.
        """
