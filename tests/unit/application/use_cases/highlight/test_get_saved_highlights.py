from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import HighlightDashboardQuery
from backend.application.use_cases.highlight.feed.get_saved_highlights import (
    GetSavedHighlightsUseCase,
)
from backend.domain import Highlight
from tests.support.fakes import FakeUnitOfWork


def _use_case(highlights) -> tuple:
    """Собрать сценарий сохранённых хайлайтов с двойниками репозиториев."""
    highlight_repository = AsyncMock()
    highlight_repository.get_saved_by_user.return_value = highlights
    highlight_repository.get_engagement_map.return_value = {}
    user_repository = AsyncMock()
    user_repository.get_by_ids.return_value = []
    anime_api_client = AsyncMock()
    anime_api_client.get_by_id.return_value = None
    uow = FakeUnitOfWork(
        HighlightRepository=highlight_repository,
        UserRepository=user_repository,
    )
    use_case = GetSavedHighlightsUseCase(uow, anime_api_client)
    return use_case, uow, highlight_repository


@pytest.mark.unit
class TestGetSavedHighlightsUseCase:
    """Юнит-тесты дашборда сохранённых хайлайтов."""

    async def test_builds_dashboard_for_current_user(self):
        """Что тестируем: забор сохранённых хайлайтов владельца дашборда.
        Что передаём: запрос с user_id=4 и один хайлайт в репозитории.
        Что ожидаем: выборка по владельцу, карточка собрана, сортировка по популярности.
        """
        highlight = Highlight(
            user_id=4,
            anime_id=10,
            episode=1,
            start_timestamp=1.0,
            end_timestamp=2.0,
        )
        highlight.id = 9
        highlight.likes_count = 3
        use_case, uow, repository = _use_case([highlight])

        dashboard = await use_case.execute(
            HighlightDashboardQuery(user_id=4, viewer_user_id=4, sort_by="popular")
        )

        repository.get_saved_by_user.assert_awaited_once_with(4)
        assert uow.commits == 1
        assert len(dashboard.items) == 1
        assert dashboard.selected_sort == "popular"

    async def test_returns_empty_dashboard_without_owner(self):
        """Что тестируем: поведение запроса без владельца.
        Что передаём: пустой запрос без user_id и viewer_user_id.
        Что ожидаем: репозиторий не вызывается, дашборд пуст.
        """
        use_case, _uow, repository = _use_case([])

        dashboard = await use_case.execute(HighlightDashboardQuery())

        repository.get_saved_by_user.assert_not_awaited()
        assert dashboard.items == []
