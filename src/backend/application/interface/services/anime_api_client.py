"""Abstract anime API client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from backend.domain.value_objects.anime.catalog_page import CatalogPage


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
        genres: Sequence[str] = (),
        media_type: str = "",
        status: str = "",
        year_from: int | None = None,
        year_to: int | None = None,
        min_score: float | None = None,
        sort: str = "rating",
        order: str = "desc",
        page: int = 1,
        per_page: int = 25,
    ) -> CatalogPage:
        """Browse anime with Anixart-like filters.

        Genre selection is applied with OR semantics on the provider side
        because neither upstream API supports conjunction. The caller is
        responsible for narrowing the returned window further when a stricter
        match mode is required.

        Args:
            genres: Genre or tag names to narrow the catalog by.
            media_type: Format filter (tv, movie, ova, ona, special). Empty means all.
            status: Status filter (airing, complete, upcoming). Empty means all.
            year_from: Optional lower bound release year.
            year_to: Optional upper bound release year.
            min_score: Optional minimum normalized rating (0-10).
            sort: Sorting strategy (rating, popularity, newest, title).
            order: Sorting direction (asc, desc).
            page: One-based page number to request.
            per_page: Number of items per page.

        Returns:
            CatalogPage: Requested page of anime with pagination metadata.
        """
