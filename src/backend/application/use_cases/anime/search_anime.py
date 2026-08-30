"""Use case for searching anime by title."""

from __future__ import annotations

from backend.application.dto.anime import SearchAnimeQuery
from backend.application.interface.services import AnimeApiClientInterface as AnimeApiClient
from backend.domain.entities.anime.anime import Anime


class SearchAnimeUseCase:
    """Search anime by title through the anime API client."""

    def __init__(self, api_client: AnimeApiClient):
        """Initialize the use case.

        Args:
            api_client: Anime API client.
        """
        self.api_client = api_client

    async def execute(self, query: SearchAnimeQuery) -> list[Anime]:
        """Return anime matching the search title.

        Args:
            query: Search query DTO.

        Returns:
            list[Anime]: Matching anime list.
        """
        if not query.title:
            return []
        return await self.api_client.search_by_title(
            title=query.title,
            limit=query.limit,
            include_adult=query.include_adult,
        )
