from __future__ import annotations

import pytest

from backend.domain import RecommendationResult
from backend.infrastructure.cache import RecommendationCache
from backend.infrastructure.cache.key_value_store import KeyValueStore


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


@pytest.mark.unit
@pytest.mark.parametrize("limit", [3, 5])
async def test_recommendation_cache_returns_saved_items(limit, recommendation_factory):
    """Проверяем, что кэш возвращает рекомендации по user_id и limit."""
    cache = RecommendationCache(store=KeyValueStore(namespace="test"), ttl_seconds=60)
    expected = [recommendation_factory(index) for index in range(1, limit + 1)]

    await cache.set(user_id=10, limit=limit, value=expected)

    assert await cache.get(user_id=10, limit=limit) == expected


@pytest.mark.unit
async def test_recommendation_cache_invalidates_only_target_user(recommendation_factory):
    """Проверяем, что invalidate_user очищает ключи только конкретного пользователя."""
    cache = RecommendationCache(store=KeyValueStore(namespace="test"), ttl_seconds=60)
    await cache.set(user_id=1, limit=5, value=[recommendation_factory(1)])
    await cache.set(user_id=2, limit=5, value=[recommendation_factory(2)])

    await cache.invalidate_user(1)

    assert await cache.get(user_id=1, limit=5) is None
    remaining = await cache.get(user_id=2, limit=5)
    assert remaining is not None
    assert [item.anime_id for item in remaining] == [2]


@pytest.mark.unit
async def test_recommendation_cache_clear_drops_everything(recommendation_factory):
    """Проверяем, что clear очищает все сохраненные рекомендации."""
    cache = RecommendationCache(store=KeyValueStore(namespace="test"), ttl_seconds=60)
    await cache.set(user_id=1, limit=5, value=[recommendation_factory(1)])
    await cache.set(user_id=2, limit=5, value=[recommendation_factory(2)])

    await cache.clear()

    assert await cache.get(user_id=1, limit=5) is None
    assert await cache.get(user_id=2, limit=5) is None
