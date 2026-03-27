from typing import List
from datetime import datetime
from src.backend.domain.anime.entity import Anime
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient


class GetSeasonPopularUseCase:
    """
    Получение популярных аниме текущего сезона через Jikan API
    """

    def __init__(self, api_client: AnimeApiClient):
        self.api_client = api_client

    def _current_season(self) -> str:
        month = datetime.now().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"

    def execute(
        self, year: int = None, season: str = None, limit: int = 10
    ) -> List[Anime]:
        """
        Получение популярных аниме
        season: 'winter', 'spring', 'summer', 'fall'
        year и season по умолчанию берутся из текущей даты
        """
        year = year or datetime.now().year
        season = season or self._current_season()
        return self.api_client.get_season_popular(year=year, season=season, limit=limit)
