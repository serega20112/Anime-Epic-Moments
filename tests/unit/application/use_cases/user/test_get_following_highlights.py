from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import HighlightDashboardQuery
from backend.application.use_cases.user.get_following_highlights import (
    GetFollowingHighlightsUseCase,
)
from backend.domain import Highlight
from backend.domain.clock import utc_now
from tests.support.fakes import FakeUnitOfWork


def _highlight() -> Highlight:
    """Собрать свежий хайлайт автора подписки."""
    highlight = Highlight(
        user_id=7,
        anime_id=18,
        episode=2,
        start_timestamp=15.0,
        end_timestamp=40.0,
        title="Эпичный старт",
        category="бой",
        description="Очень мощный момент",
        emotion="hype",
        created_at=utc_now() - timedelta(hours=2),
    )
    highlight.id = 101
    highlight.likes_count = 12
    highlight.views_count = 44
    return highlight


def _use_case(highlights) -> tuple:
    """Собрать сценарий ленты подписок с двойниками репозиториев."""
    followed = SimpleNamespace(
        id=7, username="creator", avatar_url="https://example.com/creator.png"
    )
    highlight_repository = AsyncMock()
    highlight_repository.get_by_users.return_value = highlights
    highlight_repository.get_engagement_map.return_value = {
        101: SimpleNamespace(comments_count=3, is_liked=False, is_saved=False)
    }
    user_repository = AsyncMock()
    user_repository.get_followed_users.return_value = [followed]
    user_repository.get_follow_stats.return_value = (0, 1)
    user_repository.get_by_ids.return_value = [followed]
    anime_api_client = AsyncMock()
    anime_api_client.get_by_id.return_value = SimpleNamespace(
        title="Gintama",
        original_title=None,
        cover_url="https://example.com/gintama.jpg",
        external_id="18",
    )
    uow = FakeUnitOfWork(
        HighlightRepository=highlight_repository,
        UserRepository=user_repository,
    )
    use_case = GetFollowingHighlightsUseCase(uow, anime_api_client)
    return use_case, uow, highlight_repository, user_repository


@pytest.mark.unit
class TestGetFollowingHighlightsUseCase:
    """Юнит-тесты ленты хайлайтов подписок."""

    @pytest.mark.parametrize("sort_by", ["recent", "popular"])
    async def test_builds_feed_with_followed_users(self, sort_by):
        """Что тестируем: карточки хайлайтов подписок и превью авторов.
        Что передаём: подписку на автора 7 и его хайлайт.
        Что ожидаем: карточка с автором, число подписок и выбранный порядок.
        """
        use_case, _uow, highlights, users = _use_case([_highlight()])

        page = await use_case.execute(
            HighlightDashboardQuery(user_id=3, sort_by=sort_by, include_spoilers=False)
        )

        users.get_followed_users.assert_awaited_once_with(3, limit=12)
        highlights.get_by_users.assert_awaited_once_with([7], limit=80)
        assert page.total_following == 1
        assert page.followed_users[0].username == "creator"
        assert page.dashboard.items[0].owner_username == "creator"
        assert page.dashboard.items[0].owner_profile_url == "/users/7"
        assert page.dashboard.items[0].anime_title == "Gintama"
        assert page.dashboard.selected_sort == sort_by

    async def test_returns_empty_page_without_viewer(self):
        """Что тестируем: поведение запроса без зрителя.
        Что передаём: запрос без user_id и viewer_user_id.
        Что ожидаем: пустая лента без обращений к репозиториям.
        """
        use_case, _uow, highlights, users = _use_case([])

        page = await use_case.execute(HighlightDashboardQuery())

        highlights.get_by_users.assert_not_awaited()
        users.get_followed_users.assert_not_awaited()
        assert page.dashboard.items == []
        assert page.followed_users == []
        assert page.total_following == 0

    async def test_truncates_feed_to_requested_limit(self):
        """Что тестируем: обрезку ленты до запрошенного размера.
        Что передаём: два хайлайта при limit=1.
        Что ожидаем: одна карточка и пересчитанный счётчик.
        """
        first = _highlight()
        second = _highlight()
        second.id = 102
        use_case, _uow, _highlights, _users = _use_case([first, second])

        page = await use_case.execute(HighlightDashboardQuery(user_id=3, limit=1))

        assert len(page.dashboard.items) == 1
        assert page.dashboard.stats.total_highlights == 1
