from __future__ import annotations

from typing import List

from src.backend.domain.recommendation.value_object import RecommendationResult
from src.backend.infrastructure.cache.ttl_cache import TTLCache


class RecommendationCache:
    """Кэширует рекомендации по пользователю на короткое время."""

    def __init__(self, ttl_seconds: float = 180.0, max_entries: int = 256):
        self._cache = TTLCache[tuple[int, int], List[RecommendationResult]](
            ttl_seconds=ttl_seconds,
            max_entries=max_entries,
        )

    def get(self, user_id: int, limit: int) -> List[RecommendationResult] | None:
        return self._cache.get((int(user_id), int(limit)))

    def set(
        self, user_id: int, limit: int, value: List[RecommendationResult]
    ) -> List[RecommendationResult]:
        return self._cache.set((int(user_id), int(limit)), list(value))

    def invalidate_user(self, user_id: int):
        target_user_id = int(user_id)
        self._cache.delete_matching(lambda key: key[0] == target_user_id)

    def clear(self):
        self._cache.clear()
