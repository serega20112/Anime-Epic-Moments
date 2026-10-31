"""Кэш обзора профиля и ИИ-описания вкусов."""

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
        """Создать кэш профиля с заданными сроками жизни записей."""
        self.store = store
        self.overview_ttl_seconds = int(overview_ttl_seconds)
        self.ai_summary_ttl_seconds = int(ai_summary_ttl_seconds)

    async def get_overview(self, user_id: int) -> ProfileOverview | None:
        """Прочитать обзор профиля из кэша."""
        return await self.store.get(await self._overview_key(user_id))

    async def set_overview(self, user_id: int, overview: ProfileOverview) -> ProfileOverview:
        """Положить обзор профиля в кэш."""
        return await self.store.set(
            await self._overview_key(user_id),
            overview,
            ttl_seconds=self.overview_ttl_seconds,
        )

    async def get_ai_summary(self, user_id: int) -> str | None:
        """Прочитать ИИ-описание вкусов из кэша."""
        return await self.store.get(await self._ai_summary_key(user_id))

    async def set_ai_summary(self, user_id: int, summary: str) -> str:
        """Положить ИИ-описание вкусов в кэш."""
        return await self.store.set(
            await self._ai_summary_key(user_id),
            str(summary or "").strip(),
            ttl_seconds=self.ai_summary_ttl_seconds,
        )

    async def invalidate_overview(self, user_id: int):
        """Сбросить закэшированный обзор профиля."""
        await self.store.delete(await self._overview_key(user_id))

    async def invalidate_user(self, user_id: int, include_ai_summary: bool = False):
        """Сбросить все закэшированные данные пользователя."""
        await self.invalidate_overview(user_id)
        if include_ai_summary:
            await self.store.delete(await self._ai_summary_key(user_id))

    async def _overview_key(self, user_id: int) -> str:
        return f"profile_overview:{int(user_id)}"

    async def _ai_summary_key(self, user_id: int) -> str:
        return f"profile_ai_summary:{int(user_id)}"
