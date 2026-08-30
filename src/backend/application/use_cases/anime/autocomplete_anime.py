"""Autocomplete use case for anime titles."""

from __future__ import annotations

from backend.application.dto.anime import AutocompleteAnimeQuery
from backend.application.interface.services import AnimeApiClientInterface as AnimeApiClient
from backend.domain.entities.anime.anime import Anime


class AutocompleteAnimeUseCase:
    """Provide anime title autocomplete suggestions."""

    def __init__(self, api_client: AnimeApiClient):
        """Initialize the use case.

        Args:
            api_client: Anime API client.
        """
        self.api_client = api_client

    async def execute(self, query: AutocompleteAnimeQuery) -> list[Anime]:
        """Return autocomplete suggestions for a partial title.

        Args:
            query: Autocomplete query DTO.

        Returns:
            list[Anime]: Matching anime suggestions.
        """
        if not query.query:
            return []
        return await self.api_client.search_by_title(
            title=query.query,
            limit=query.limit,
            include_adult=query.include_adult,
        )
