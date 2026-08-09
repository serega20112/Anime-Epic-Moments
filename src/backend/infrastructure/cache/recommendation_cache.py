from __future__ import annotations

from backend.domain import RecommendationResult
from backend.infrastructure.cache.key_value_store import KeyValueStore


class RecommendationCache:
    """Кэширует рекомендации по пользователю на короткое время."""

    def __init__(
            self,
            store: KeyValueStore | None = None,
            ttl_seconds: float = 180.0,
            max_entries: int | None = None,
    ):
        self.store = store or KeyValueStore(redis_url=None, namespace="recommendation")
        self.ttl_seconds = max(int(ttl_seconds), 1)
        self.prefix = "recommendation"

    async def get(self, user_id: int, limit: int) -> list[RecommendationResult] | None:
        return await self.store.get(self._key(user_id=user_id, limit=limit))

    async def set(
            self, user_id: int, limit: int, value: list[RecommendationResult]
    ) -> list[RecommendationResult]:
        return await self.store.set(
            self._key(user_id=user_id, limit=limit),
            list(value),
            ttl_seconds=self.ttl_seconds,
        )

    async def invalidate_user(self, user_id: int):
        target_user_id = int(user_id)
        await self.store.delete_prefix(f"{self.prefix}:{target_user_id}:")

    async def clear(self):
        await self.store.delete_prefix(f"{self.prefix}:")

    def _key(self, user_id: int, limit: int) -> str:
        return f"{self.prefix}:{int(user_id)}:{int(limit)}"
