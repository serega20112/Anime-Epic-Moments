from typing import List
from src.backend.domain.anime.entity import Anime
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient


class AutocompleteAnimeUseCase:
    """
    Автокомплит поиска аниме по названию
    """

    def __init__(self, api_client: AnimeApiClient):
        self.api_client = api_client

    def execute(self, query: str, limit: int = 5) -> List[Anime]:
        """
        Возвращает список аниме для автокомплита
        """
        return self.api_client.search_by_title(title=query, limit=limit)
