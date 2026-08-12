from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.application.services.recommendation_service import RecommendationService
from backend.infrastructure.cache import RecommendationCache


@pytest.mark.unit
class TestRecommendationService:
    """Юнит-тесты сервиса генерации рекомендаций."""

    def test_returns_cached_items_without_hitting_repositories(self):
        """Что тестируем: cache hit не запускает репозитории и внешние API заново.
        Что передаём: пользователя с ранее закэшированными рекомендациями.
        Что ожидаем: возвращается кэш, а репозитории/клиент не вызываются.
        """
        cache = RecommendationCache(ttl_seconds=60, max_entries=8)
        cached_item = SimpleNamespace(anime_id=7, title="Cached")
        cache.set(user_id=1, limit=5, value=[cached_item])
        favorite_repo = Mock()
        highlight_repo = Mock()
        anime_client = Mock()
        service = RecommendationService(favorite_repo, highlight_repo, anime_client, cache)

        result = service.generate(user_id=1, limit=5)

        assert result == [cached_item]
        favorite_repo.get_by_user.assert_not_called()
        highlight_repo.get_by_user.assert_not_called()
        anime_client.get_top_anime.assert_not_called()

    @pytest.mark.parametrize(
        ("force_refresh", "expected_calls"),
        [(False, 0), (True, 1)],
    )
    def test_respects_force_refresh(self, force_refresh, expected_calls, anime_factory):
        """Что тестируем: force_refresh обходит кэш и пересчитывает рекомендации.
        Что передаём: force_refresh=True/False при наличии кэша.
        Что ожидаем: при force_refresh перезапрос топ-аниме и свежий результат, иначе кэш.
        """
        cache = RecommendationCache(ttl_seconds=60, max_entries=8)
        cached_item = SimpleNamespace(anime_id=9, title="Cached")
        cache.set(user_id=1, limit=3, value=[cached_item])
        favorite_repo = Mock()
        highlight_repo = Mock()
        anime_client = Mock()
        anime_client.get_top_anime.return_value = [anime_factory(external_id="101", title="Fresh")]
        service = RecommendationService(favorite_repo, highlight_repo, anime_client, cache)

        favorite_repo.get_by_user.return_value = [SimpleNamespace(anime_id=555, genres=["Action"])]
        highlight_repo.get_by_user.return_value = []

        result = service.generate(user_id=1, limit=3, force_refresh=force_refresh)

        assert anime_client.get_top_anime.call_count == expected_calls
        if force_refresh:
            assert result[0].title == "Fresh"
        else:
            assert result == [cached_item]

    def test_caches_empty_result(self):
        """Что тестируем: пустой результат тоже кэшируется и не пересчитывается сразу повторно.
        Что передаём: два последовательных запроса, не дающих рекомендаций.
        Что ожидаем: репозитории вызываются один раз, возвращается пустой список.
        """
        cache = RecommendationCache(ttl_seconds=60, max_entries=8)
        favorite_repo = Mock()
        highlight_repo = Mock()
        anime_client = Mock()
        service = RecommendationService(favorite_repo, highlight_repo, anime_client, cache)
        favorite_repo.get_by_user.return_value = []
        highlight_repo.get_by_user.return_value = []

        first = service.generate(user_id=2, limit=5)
        second = service.generate(user_id=2, limit=5)

        assert first == []
        assert second == []
        favorite_repo.get_by_user.assert_called_once_with(2)
        highlight_repo.get_by_user.assert_called_once_with(2)

    def test_invalidate_user_clears_cached_entries(self):
        """Что тестируем: invalidate_user удаляет сохраненный результат пользователя.
        Что передаём: пользователя с закэшированными рекомендациями.
        Что ожидаем: после invalidate кэш для этого пользователя пуст.
        """
        cache = RecommendationCache(ttl_seconds=60, max_entries=8)
        cache.set(user_id=3, limit=5, value=[SimpleNamespace(anime_id=3)])
        service = RecommendationService(Mock(), Mock(), Mock(), cache)

        service.invalidate_user(3)

        assert cache.get(user_id=3, limit=5) is None