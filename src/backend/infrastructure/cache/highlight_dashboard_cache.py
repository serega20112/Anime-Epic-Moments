from __future__ import annotations

from backend.domain import HighlightDashboard
from backend.infrastructure.cache.key_value_store import KeyValueStore


class HighlightDashboardCache:
    """Кэширует публичный дашборд хайлайтов на короткое время."""

    def __init__(
            self,
            store: KeyValueStore,
            ttl_seconds: float = 120.0,
    ):
        self.store = store
        self.ttl_seconds = max(int(ttl_seconds), 1)
        self.prefix = "highlight_dashboard:public"

    async def get_public(
            self,
            limit: int,
            anime_id: int | None,
            emotion: str | None,
            category: str | None,
            sort_by: str,
            created_date: str | None,
            query: str | None,
            include_spoilers: bool,
    ) -> HighlightDashboard | None:
        return await self.store.get(
            self._key(
                limit=limit,
                anime_id=anime_id,
                emotion=emotion,
                category=category,
                sort_by=sort_by,
                created_date=created_date,
                query=query,
                include_spoilers=include_spoilers,
            )
        )

    async def set_public(
            self,
            limit: int,
            anime_id: int | None,
            emotion: str | None,
            category: str | None,
            sort_by: str,
            created_date: str | None,
            query: str | None,
            include_spoilers: bool,
            value: HighlightDashboard,
    ) -> HighlightDashboard:
        return await self.store.set(
            self._key(
                limit=limit,
                anime_id=anime_id,
                emotion=emotion,
                category=category,
                sort_by=sort_by,
                created_date=created_date,
                query=query,
                include_spoilers=include_spoilers,
            ),
            value,
            ttl_seconds=self.ttl_seconds,
        )

    async def invalidate_public(self):
        await self.store.delete_prefix(f"{self.prefix}:")

    def _key(
        self,
        limit: int,
        anime_id: int | None,
        emotion: str | None,
        category: str | None,
        sort_by: str,
        created_date: str | None,
        query: str | None,
        include_spoilers: bool,
    ) -> str:
        return (
            f"{self.prefix}:{int(limit)}:{anime_id}:{emotion or ''}:"
            f"{category or ''}:{sort_by}:{created_date or ''}:{query or ''}:{int(include_spoilers)}"
        )
