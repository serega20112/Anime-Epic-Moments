from backend.domain import ProfileOverview
from backend.infrastructure.cache.key_value_store import KeyValueStore


class ProfileOverviewCache:
    """Кэширует profile overview и AI-сводку вкуса пользователя."""

    def __init__(
        self,
        store: KeyValueStore,
        overview_ttl_seconds: int = 180,
        ai_summary_ttl_seconds: int = 1800,
    ):
        self.store = store
        self.overview_ttl_seconds = int(overview_ttl_seconds)
        self.ai_summary_ttl_seconds = int(ai_summary_ttl_seconds)

    async def get_overview(self, user_id: int) -> ProfileOverview | None:
        return await self.store.get(self._overview_key(user_id))

    async def set_overview(self, user_id: int, overview: ProfileOverview) -> ProfileOverview:
        return await self.store.set(
            self._overview_key(user_id),
            overview,
            ttl_seconds=self.overview_ttl_seconds,
        )

    async def get_ai_summary(self, user_id: int) -> str | None:
        return await self.store.get(self._ai_summary_key(user_id))

    async def set_ai_summary(self, user_id: int, summary: str) -> str:
        return await self.store.set(
            self._ai_summary_key(user_id),
            str(summary or "").strip(),
            ttl_seconds=self.ai_summary_ttl_seconds,
        )

    async def invalidate_overview(self, user_id: int):
        await self.store.delete(self._overview_key(user_id))

    async def invalidate_user(self, user_id: int, include_ai_summary: bool = False):
        await self.invalidate_overview(user_id)
        if include_ai_summary:
            await self.store.delete(self._ai_summary_key(user_id))

    def _overview_key(self, user_id: int) -> str:
        return f"profile_overview:{int(user_id)}"

    def _ai_summary_key(self, user_id: int) -> str:
        return f"profile_ai_summary:{int(user_id)}"
