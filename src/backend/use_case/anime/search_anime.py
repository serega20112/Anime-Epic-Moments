from typing import List
from src.backend.domain.anime.entity import Anime
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient


class SearchAnimeUseCase:
    """
    Поиск аниме по названию через AnimeApiClient
    """

    def __init__(self, api_client: AnimeApiClient):
        self.api_client = api_client

    def execute(self, title: str, limit: int = 10) -> List[Anime]:
        """
        Возвращает список объектов Anime, найденных по названию
        """
        return self.api_client.search_by_title(title=title, limit=limit)
