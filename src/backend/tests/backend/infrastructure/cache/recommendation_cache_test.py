from __future__ import annotations

import pytest

from src.backend.domain.recommendation.value_object import RecommendationResult
from src.backend.infrastructure.cache.key_value_store import KeyValueStore
from src.backend.infrastructure.cache.recommendation_cache import RecommendationCache


@pytest.fixture
def recommendation_factory():
    """Создает RecommendationResult с минимально нужными полями."""

    def _build(anime_id: int):
        return RecommendationResult(
            anime_id=anime_id,
            reason="match",
            similarity_score=0.95,
            title=f"Anime {anime_id}",
            description="desc",
            image_url=None,
            genres=["Action"],
            watch_url=f"/watch/{anime_id}?episode=1",
        )

    return _build


@pytest.mark.parametrize("limit", [3, 5])
def test_recommendation_cache_returns_saved_items(limit, recommendation_factory):
    """Проверяем, что кэш возвращает рекомендации по user_id и limit."""
    cache = RecommendationCache(store=KeyValueStore(namespace="test"), ttl_seconds=60)
    expected = [recommendation_factory(index) for index in range(1, limit + 1)]

    cache.set(user_id=10, limit=limit, value=expected)

    assert cache.get(user_id=10, limit=limit) == expected


def test_recommendation_cache_invalidates_only_target_user(recommendation_factory):
    """Проверяем, что invalidate_user очищает ключи только конкретного пользователя."""
    cache = RecommendationCache(store=KeyValueStore(namespace="test"), ttl_seconds=60)
    cache.set(user_id=1, limit=5, value=[recommendation_factory(1)])
    cache.set(user_id=2, limit=5, value=[recommendation_factory(2)])

    cache.invalidate_user(1)

    assert cache.get(user_id=1, limit=5) is None
    remaining = cache.get(user_id=2, limit=5)
    assert remaining is not None
    assert [item.anime_id for item in remaining] == [2]


def test_recommendation_cache_clear_drops_everything(recommendation_factory):
    """Проверяем, что clear очищает все сохраненные рекомендации."""
    cache = RecommendationCache(store=KeyValueStore(namespace="test"), ttl_seconds=60)
    cache.set(user_id=1, limit=5, value=[recommendation_factory(1)])
    cache.set(user_id=2, limit=5, value=[recommendation_factory(2)])

    cache.clear()

    assert cache.get(user_id=1, limit=5) is None
    assert cache.get(user_id=2, limit=5) is None
