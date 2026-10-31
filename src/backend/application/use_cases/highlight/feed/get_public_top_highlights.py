"""Сценарий публичного топа хайлайтов."""

from __future__ import annotations

from dataclasses import replace

from backend.application.dto import HighlightDashboardQuery
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.services import (
    AnimeApiClientInterface,
    HighlightDashboardCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.highlight.feed.get_user_highlights import (
    GetUserHighlightsUseCase,
)
from backend.domain import Highlight, HighlightDashboard


class GetPublicTopHighlightsUseCase(GetUserHighlightsUseCase):
    """Возвращает публичный топ хайлайтов в формате дашборда."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClientInterface,
        highlight_dashboard_cache: HighlightDashboardCacheInterface,
    ) -> None:
        """Инициализирует сценарий получения публичного топа хайлайтов.

        Args:
            unit_of_work: Граница транзакции для чтения хайлайтов и авторов.
            anime_api_client: Клиент API аниме для заголовков карточек.
            highlight_dashboard_cache: Кэш публичного дашборда для анонимных зрителей.
        """
        super().__init__(unit_of_work, anime_api_client)
        self._highlight_dashboard_cache = highlight_dashboard_cache

    async def execute(self, query: HighlightDashboardQuery) -> HighlightDashboard:
        """Возвращает публичный топ хайлайтов.

        Кэш используется только для анонимных зрителей: у авторизованного зрителя
        карточки содержат персональные отметки лайков и сохранений.

        Args:
            query: Фильтры, сортировка и зритель дашборда.

        Returns:
            HighlightDashboard: Дашборд публичного топа.
        """
        sort_by = query.sort_by if query.sort_by in {"popular", "recent"} else "popular"
        normalized = replace(query, sort_by=sort_by)
        use_cache = query.viewer_user_id is None
        if use_cache:
            cached = await self._highlight_dashboard_cache.get_public(
                limit=normalized.limit,
                anime_id=normalized.anime_id,
                emotion=normalized.emotion,
                category=normalized.category,
                sort_by=sort_by,
                created_date=normalized.created_date,
                query=normalized.query,
                include_spoilers=normalized.include_spoilers,
            )
            if cached is not None:
                return cached
        dashboard = await super().execute(normalized)
        if use_cache:
            await self._highlight_dashboard_cache.set_public(
                limit=normalized.limit,
                anime_id=normalized.anime_id,
                emotion=normalized.emotion,
                category=normalized.category,
                sort_by=sort_by,
                created_date=normalized.created_date,
                query=normalized.query,
                include_spoilers=normalized.include_spoilers,
                value=dashboard,
            )
        return dashboard

    async def _load(
        self,
        repository: HighlightRepository,
        query: HighlightDashboardQuery,
    ) -> list[Highlight]:
        """Загрузить публичные хайлайты в выбранной сортировке.

        Args:
            repository: Репозиторий хайлайтов текущей транзакции.
            query: Параметры дашборда с нормализованной сортировкой.

        Returns:
            list[Highlight]: Топ по лайкам либо последние хайлайты.
        """
        if query.sort_by == "popular":
            return await repository.get_public_top(query.limit)
        return await repository.get_public_recent(query.limit)
