"""Ключ-значения и кэши: Redis-store, кэши дашборда, профиля и источников."""

from __future__ import annotations

from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from backend.config import Settings
from backend.infrastructure.cache import HighlightDashboardCache, RecommendationCache
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.cache.security_store import SecurityKeyValueStore
from backend.infrastructure.cache.watch_source_caches import WatchSourceCaches


class CacheProvidersMixin(Provider):
    """Ключ-значения и кэши: Redis-store, кэши дашборда, профиля и источников.

    Часть провайдера: методы `@provide` собираются dishka из базовых
    классов, поэтому mixin самодостаточен и наследует `Provider`.
    """

    @provide(scope=Scope.APP)
    async def key_value_store(self) -> AsyncIterator[KeyValueStore]:
        """Создать хранилище «ключ-значение»."""
        store = KeyValueStore(
            redis_url=Settings.redis_url,
            namespace="anime_epic_moments",
            required=Settings.redis_required,
        )
        yield store
        await store.close()

    @provide(scope=Scope.APP)
    async def security_key_value_store(self) -> AsyncIterator[SecurityKeyValueStore]:
        """Создать хранилище состояния безопасности, падающее при отказе бэкенда."""
        store = SecurityKeyValueStore(
            redis_url=Settings.redis_url,
            namespace="anime_epic_moments",
        )
        yield store
        await store.close()

    @provide(scope=Scope.APP)
    async def recommendation_cache(self, store: KeyValueStore) -> RecommendationCache:
        """Создать кэш рекомендаций."""
        return RecommendationCache(store=store)

    @provide(scope=Scope.APP)
    async def highlight_dashboard_cache(self, store: KeyValueStore) -> HighlightDashboardCache:
        """Создать кэш сводки хайлайтов."""
        return HighlightDashboardCache(store=store)

    @provide(scope=Scope.APP)
    async def profile_overview_cache(self, store: KeyValueStore) -> ProfileOverviewCache:
        """Создать кэш обзора профиля."""
        return ProfileOverviewCache(store=store)

    @provide(scope=Scope.APP)
    async def watch_source_caches(self) -> WatchSourceCaches:
        """Создать внутрипроцессные кэши источников просмотра.

        Returns:
            WatchSourceCaches: Кэши, живущие всё приложение: сервис
            синхронизации собирается на каждый запрос, и его кэш должен
            переживать запросы, иначе TTL не имеет смысла.
        """
        return WatchSourceCaches.create()
