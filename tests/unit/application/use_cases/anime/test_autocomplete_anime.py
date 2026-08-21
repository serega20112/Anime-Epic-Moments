from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto.anime import AutocompleteAnimeQuery
from backend.application.use_cases.anime.autocomplete_anime import AutocompleteAnimeUseCase


@pytest.mark.unit
class TestAutocompleteAnimeUseCase:
    """Юнит-тесты автодополнения названий аниме."""

    async def test_delegates_to_title_search(self, anime_factory):
        """Что тестируем: передачу запроса в title search с нужным limit.
        Что передаём: AutocompleteAnimeQuery с частичным названием.
        Что ожидаем: api_client вызван с title и limit, возвращается список.
        """
        api_client = AsyncMock()
        api_client.search_by_title.return_value = [anime_factory(title="Gintama")]
        use_case = AutocompleteAnimeUseCase(api_client)

        result = await use_case.execute(AutocompleteAnimeQuery(query="gin", limit=3))

        assert [item.title for item in result] == ["Gintama"]
        api_client.search_by_title.assert_awaited_once_with(title="gin", limit=3)

    async def test_returns_empty_for_blank_query(self):
        """Что тестируем: отсутствие вызова при пустом запросе.
        Что передаём: пустую строку.
        Что ожидаем: пустой список без обращения к API.
        """
        api_client = AsyncMock()
        use_case = AutocompleteAnimeUseCase(api_client)

        result = await use_case.execute(AutocompleteAnimeQuery(query="", limit=3))

        assert result == []
        api_client.search_by_title.assert_not_awaited()
