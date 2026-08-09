from __future__ import annotations

from unittest.mock import Mock

from backend.application.use_cases.anime.autocomplete_anime import AutocompleteAnimeUseCase


def test_autocomplete_anime_delegates_to_title_search(anime_factory):
    """Проверяем, что AutocompleteAnimeUseCase вызывает title search с нужным limit."""
    api_client = Mock()
    api_client.search_by_title.return_value = [anime_factory(title="Gintama")]
    use_case = AutocompleteAnimeUseCase(api_client)

    result = use_case.execute("gin", limit=3)

    assert [item.title for item in result] == ["Gintama"]
    api_client.search_by_title.assert_called_once_with(title="gin", limit=3)
