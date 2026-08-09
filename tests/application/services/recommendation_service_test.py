from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.application.services.recommendation_service import RecommendationService
from backend.infrastructure.cache import RecommendationCache


def test_recommendation_service_returns_cached_items_without_hitting_repositories():
    """Проверяем, что cache hit не запускает репозитории и внешние API заново."""
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
def test_recommendation_service_respects_force_refresh(force_refresh, expected_calls, anime_factory):
    """Проверяем, что force_refresh обходит кэш и пересчитывает рекомендации."""
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


def test_recommendation_service_caches_empty_result():
    """Проверяем, что пустая рекомендация тоже кэшируется и не пересчитывается сразу повторно."""
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


def test_recommendation_service_invalidate_user_clears_cached_entries():
    """Проверяем, что invalidate_user удаляет сохраненный результат пользователя."""
    cache = RecommendationCache(ttl_seconds=60, max_entries=8)
    cache.set(user_id=3, limit=5, value=[SimpleNamespace(anime_id=3)])
    service = RecommendationService(Mock(), Mock(), Mock(), cache)

    service.invalidate_user(3)

    assert cache.get(user_id=3, limit=5) is None
