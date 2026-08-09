"""Use case for fetching popular anime of a season."""

from __future__ import annotations

from datetime import datetime

from backend.application.dto.anime_queries import GetSeasonPopularQuery
from backend.domain.anime.entity import Anime
from backend.domain.exceptions import ValidationError
from backend.domain.services import AnimeApiClientInterface as AnimeApiClient

_VALID_SEASONS = {"winter", "spring", "summer", "fall"}


class GetSeasonPopularUseCase:
    """Fetch popular anime for a given season and year."""

    def __init__(self, api_client: AnimeApiClient):
        """Initialize the use case.

        Args:
            api_client: Anime API client.
        """
        self.api_client = api_client

    def _current_season(self) -> str:
        """Determine the current season name from the current month.

        Returns:
            str: Season name (winter, spring, summer, fall).
        """
        month = datetime.now().month
        if month in (12, 1, 2):
            return "winter"
        if month in (3, 4, 5):
            return "spring"
        if month in (6, 7, 8):
            return "summer"
        return "fall"

    async def execute(self, query: GetSeasonPopularQuery) -> list[Anime]:
        """Return popular anime for the requested season.

        Args:
            query: Season popular query DTO.

        Returns:
            list[Anime]: Popular anime list.

        Raises:
            ValidationError: If the season name is invalid.
        """
        year = query.year or datetime.now().year
        season = query.season or self._current_season()
        if season not in _VALID_SEASONS:
            raise ValidationError(f"Invalid season: {season}")
        return await self.api_client.get_season_popular(
            year=year,
            season=season,
            limit=query.limit,
        )
