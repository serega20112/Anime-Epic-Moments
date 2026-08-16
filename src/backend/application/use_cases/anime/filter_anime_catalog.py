"""Use case for browsing anime through Anixart-style filters."""

from __future__ import annotations

from backend.application.dto.anime_queries import FilterAnimeCatalogQuery
from backend.domain.anime.entity import Anime
from backend.domain.services import AnimeApiClientInterface as AnimeApiClient


class FilterAnimeCatalogUseCase:
    """Browse anime by genre, format, status, year, rating and sort."""

    def __init__(self, api_client: AnimeApiClient):
        """Initialize the use case.

        Args:
            api_client: Anime API client.
        """
        self.api_client = api_client

    async def execute(self, query: FilterAnimeCatalogQuery) -> list[Anime]:
        """Return anime matching the requested filters.

        Args:
            query: Filter query DTO.

        Returns:
            list[Anime]: Matching anime list.
        """
        return await self.api_client.filter_catalog(
            genre=query.genre,
            media_type=query.media_type,
            status=query.status,
            year_from=query.year_from,
            year_to=query.year_to,
            min_score=query.min_score,
            sort=query.sort,
            order=query.order,
            limit=query.limit,
        )
