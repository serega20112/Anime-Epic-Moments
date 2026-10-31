from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import HighlightDashboardQuery
from backend.application.use_cases import GetPublicTopHighlightsUseCase
from backend.domain import Highlight, HighlightDashboard, HighlightStats
from tests.support.fakes import FakeUnitOfWork


def _highlight(highlight_id: int) -> Highlight:
    """Собрать публичный хайлайт с указанным идентификатором."""
    highlight = Highlight(
        user_id=1,
        anime_id=10,
        episode=1,
        start_timestamp=1.0,
        end_timestamp=2.0,
    )
    highlight.id = highlight_id
    return highlight


def _use_case(highlights) -> tuple:
    """Собрать сценарий публичного топа с двойниками зависимостей."""
    highlight_repository = AsyncMock()
    highlight_repository.get_public_top.return_value = highlights
    highlight_repository.get_public_recent.return_value = highlights
    highlight_repository.get_engagement_map.return_value = {}
    user_repository = AsyncMock()
    user_repository.get_by_ids.return_value = []
    anime_api_client = AsyncMock()
    anime_api_client.get_by_id.return_value = None
    dashboard_cache = AsyncMock()
    dashboard_cache.get_public.return_value = None
    uow = FakeUnitOfWork(
        HighlightRepository=highlight_repository,
        UserRepository=user_repository,
    )
    use_case = GetPublicTopHighlightsUseCase(uow, anime_api_client, dashboard_cache)
    return use_case, uow, highlight_repository, dashboard_cache


@pytest.mark.unit
class TestGetPublicTopHighlightsUseCase:
    """Юнит-тесты публичного топа хайлайтов."""

    async def test_uses_popularity_or_recency_query(self):
        """Что тестируем: выбор запроса в зависимости от сортировки.
        Что передаём: sort_by popular и recent с авторизованным зрителем.
        Что ожидаем: вызван соответствующий метод репозитория с limit.
        """
        use_case, _uow, repository, dashboard_cache = _use_case([_highlight(1)])

        popular = await use_case.execute(
            HighlightDashboardQuery(limit=12, sort_by="popular", viewer_user_id=7)
        )
        recent = await use_case.execute(
            HighlightDashboardQuery(limit=9, sort_by="recent", viewer_user_id=7)
        )

        repository.get_public_top.assert_awaited_once_with(12)
        repository.get_public_recent.assert_awaited_once_with(9)
        assert popular.selected_sort == "popular"
        assert recent.selected_sort == "recent"
        dashboard_cache.get_public.assert_not_awaited()

    async def test_normalizes_unknown_sort_to_popular(self):
        """Что тестируем: нормализацию неизвестной сортировки.
        Что передаём: sort_by=unknown.
        Что ожидаем: выбран топ по лайкам, а не последние хайлайты.
        """
        use_case, _uow, repository, _cache = _use_case([])

        dashboard = await use_case.execute(
            HighlightDashboardQuery(limit=5, sort_by="unknown", viewer_user_id=7)
        )

        repository.get_public_top.assert_awaited_once_with(5)
        repository.get_public_recent.assert_not_awaited()
        assert dashboard.selected_sort == "popular"

    async def test_uses_sort_in_cache_key(self):
        """Что тестируем: участие фильтров в ключе кэша публичного дашборда.
        Что передаём: анонимного зрителя и сортировку recent.
        Что ожидаем: кэш прочитан и записан с теми же фильтрами.
        """
        use_case, _uow, _repository, dashboard_cache = _use_case([_highlight(1)])

        dashboard = await use_case.execute(
            HighlightDashboardQuery(limit=6, sort_by="recent", include_spoilers=False)
        )

        dashboard_cache.get_public.assert_awaited_once_with(
            limit=6,
            anime_id=None,
            emotion=None,
            category=None,
            sort_by="recent",
            created_date=None,
            query=None,
            include_spoilers=False,
        )
        cached = dashboard_cache.set_public.await_args
        assert cached.kwargs["limit"] == 6
        assert cached.kwargs["sort_by"] == "recent"
        assert cached.kwargs["value"] is dashboard

    async def test_returns_cached_dashboard_without_repositories(self):
        """Что тестируем: отдачу готового дашборда из кэша.
        Что передаём: кэш, возвращающий собранный дашборд.
        Что ожидаем: репозитории не вызваны, результат — значение кэша.
        """
        use_case, _uow, repository, dashboard_cache = _use_case([])
        cached_dashboard = HighlightDashboard(
            items=[],
            anime_groups=[],
            emotions=[],
            categories=[],
            stats=HighlightStats(0, "Нет данных", 0.0),
            selected_anime_id=None,
            selected_emotion=None,
            selected_category=None,
            selected_sort="popular",
            selected_date=None,
            selected_query=None,
            include_spoilers=False,
        )
        dashboard_cache.get_public.return_value = cached_dashboard

        result = await use_case.execute(HighlightDashboardQuery(limit=6, sort_by="popular"))

        assert result is cached_dashboard
        repository.get_public_top.assert_not_awaited()
        dashboard_cache.set_public.assert_not_awaited()
