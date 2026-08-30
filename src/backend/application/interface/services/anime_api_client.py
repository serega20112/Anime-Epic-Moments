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

    @abstractmethod
    async def filter_catalog(
        self,
        *,
        genre: str = "",
        media_type: str = "",
        status: str = "",
        year_from: int | None = None,
        year_to: int | None = None,
        min_score: float | None = None,
        sort: str = "rating",
        order: str = "desc",
        limit: int = 30,
    ) -> list[Any]:
        """Browse anime with Anixart-like filters.

        Args:
            genre: Comma-separated genre/tag names or empty string for all.
            media_type: Format filter (tv, movie, ova, ona, special). Empty means all.
            status: Status filter (airing, complete, upcoming). Empty means all.
            year_from: Optional lower bound release year.
            year_to: Optional upper bound release year.
            min_score: Optional minimum normalized rating (0-10).
            sort: Sorting strategy (rating, popularity, newest, title).
            order: Sorting direction (asc, desc).
            limit: Maximum number of results to return.

        Returns:
            list[Any]: Filtered and sorted anime.
        """
