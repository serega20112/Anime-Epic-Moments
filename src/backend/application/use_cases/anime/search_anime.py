"""Сценарий поиска аниме по названию."""

from __future__ import annotations

from backend.application.dto.anime import SearchAnimeQuery
from backend.application.interface.services import AnimeApiClientInterface
from backend.domain.entities.anime.anime import Anime


class SearchAnimeUseCase:
    """Сценарий поиска аниме по названию через клиент каталога."""

    def __init__(self, api_client: AnimeApiClientInterface) -> None:
        """Инициализирует сценарий поиска аниме по названию.

        Args:
            api_client: Клиент API аниме.
        """
        self._api_client = api_client

    async def execute(self, query: SearchAnimeQuery) -> list[Anime]:
        """Вернуть аниме, соответствующие запросу по названию.

        Args:
            query: Запрос поиска.

        Returns:
            list[Anime]: Список подходящих аниме.
        """
        if not query.title:
            return []
        return await self._api_client.search_by_title(
            title=query.title,
            limit=query.limit,
            include_adult=query.include_adult,
        )
