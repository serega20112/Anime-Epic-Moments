from __future__ import annotations

from unittest.mock import Mock

from backend.application.use_cases import SearchAnimeUseCase


def test_search_anime_delegates_to_title_search(anime_factory):
    """Проверяем, что SearchAnimeUseCase вызывает search_by_title на API-клиенте."""
    api_client = Mock()
    api_client.search_by_title.return_value = [anime_factory(title="Initial D")]
    use_case = SearchAnimeUseCase(api_client)

    result = use_case.execute("initial", limit=6)

    assert [item.title for item in result] == ["Initial D"]
    api_client.search_by_title.assert_called_once_with(title="initial", limit=6)
