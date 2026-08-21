from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto.anime import SearchAnimeQuery
from backend.application.use_cases.anime.search_anime import SearchAnimeUseCase


@pytest.mark.unit
class TestSearchAnimeUseCase:
    """Юнит-тесты поиска аниме по названию."""

    async def test_delegates_to_title_search(self, anime_factory):
        """Что тестируем: передачу названия в search_by_title.
        Что передаём: SearchAnimeQuery с названием и лимитом.
        Что ожидаем: api_client вызван, возвращается список аниме.
        """
        api_client = AsyncMock()
        api_client.search_by_title.return_value = [anime_factory(title="Initial D")]
        use_case = SearchAnimeUseCase(api_client)

        result = await use_case.execute(SearchAnimeQuery(title="initial", limit=6))

        assert [item.title for item in result] == ["Initial D"]
        api_client.search_by_title.assert_awaited_once_with(title="initial", limit=6)

    async def test_returns_empty_for_blank_title(self):
        """Что тестируем: отсутствие запроса при пустом названии.
        Что передаём: пустую строку title.
        Что ожидаем: пустой список без обращения к API.
        """
        api_client = AsyncMock()
        use_case = SearchAnimeUseCase(api_client)

        result = await use_case.execute(SearchAnimeQuery(title="", limit=6))

        assert result == []
        api_client.search_by_title.assert_not_awaited()
