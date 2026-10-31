"""Сценарий автодополнения заголовков аниме."""

from __future__ import annotations

from backend.application.dto.anime import AutocompleteAnimeQuery
from backend.application.interface.services import AnimeApiClientInterface
from backend.domain.entities.anime.anime import Anime


class AutocompleteAnimeUseCase:
    """Сценарий подсказок названий аниме при вводе."""

    def __init__(self, api_client: AnimeApiClientInterface) -> None:
        """Инициализирует сценарий автодополнения заголовков аниме.

        Args:
            api_client: Клиент API аниме.
        """
        self._api_client = api_client

    async def execute(self, query: AutocompleteAnimeQuery) -> list[Anime]:
        """Вернуть автодополнения заголовков по частичному запросу.

        Args:
            query: Запрос автодополнения.

        Returns:
            list[Anime]: Подходящие предложения аниме.
        """
        if not query.query:
            return []
        return await self._api_client.search_by_title(
            title=query.query,
            limit=query.limit,
            include_adult=query.include_adult,
        )
