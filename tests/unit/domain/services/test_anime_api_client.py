from __future__ import annotations

from backend.domain.services.anime_api_client import AnimeApiClientInterface


class TestAnimeApiClientInterface:
    def test_is_abstract(self):
        assert isinstance(AnimeApiClientInterface.__abstractmethods__, frozenset)

    def test_abstract_method_names(self):
        assert {"get_by_id", "search", "autocomplete", "get_season_popular"} <= set(
            AnimeApiClientInterface.__abstractmethods__
        )

    def test_cannot_be_instantiated(self):
        try:
            AnimeApiClientInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True