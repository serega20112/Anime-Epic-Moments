from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import HighlightDashboardQuery
from backend.application.use_cases.highlight.feed.get_user_highlights import (
    GetUserHighlightsUseCase,
)
from backend.domain import Highlight, HighlightEngagement
from tests.support.fakes import FakeUnitOfWork


def _highlight(**overrides) -> Highlight:
    """Собрать хайлайт автора 1 с переопределёнными полями."""
    fields = {
        "user_id": 1,
        "anime_id": 10,
        "episode": 2,
        "start_timestamp": 10.0,
        "end_timestamp": 25.0,
        "title": "First",
        "category": "драма",
        "description": "best joke",
        "emotion": "funny",
        "created_at": datetime(2026, 3, 28),
    }
    fields.update(overrides)
    return Highlight(**fields)


def _use_case(highlights, *, engagement=None, users=None, anime=None) -> tuple:
    """Собрать сценарий дашборда с двойниками репозиториев и клиента аниме."""
    highlight_repository = AsyncMock()
    highlight_repository.get_by_user.return_value = highlights
    highlight_repository.get_engagement_map.return_value = engagement or {}
    user_repository = AsyncMock()
    user_repository.get_by_ids.return_value = users or []
    anime_api_client = AsyncMock()
    anime_api_client.get_by_id.return_value = anime
    uow = FakeUnitOfWork(
        HighlightRepository=highlight_repository,
        UserRepository=user_repository,
    )
    use_case = GetUserHighlightsUseCase(uow, anime_api_client)
    return use_case, uow, highlight_repository, user_repository, anime_api_client


@pytest.mark.unit
class TestGetUserHighlightsUseCase:
    """Юнит-тесты личного дашборда хайлайтов."""

    async def test_builds_dashboard_with_filters_stats_and_sort(self, anime_factory):
        """Что тестируем: фильтрацию, статистику и сортировку по популярности.
        Что передаём: два хайлайта одного аниме и фильтры по эмоции, категории, поиску.
        Что ожидаем: карточки отсортированы по лайкам, статистика посчитана.
        """
        first = _highlight()
        first.id = 7
        first.likes_count = 1
        first.views_count = 1
        second = _highlight(
            episode=3,
            start_timestamp=5.0,
            end_timestamp=10.0,
            title="Second",
            description="best joke too",
            created_at=datetime(2026, 3, 29),
        )
        second.id = 8
        second.likes_count = 4
        second.views_count = 3
        anime = anime_factory(
            external_id="185", title="Initial D", cover_url="https://example.com/cover.jpg"
        )
        use_case, _uow, _repository, _users, anime_api_client = _use_case(
            [first, second], anime=anime
        )
        anime_api_client.get_by_id.side_effect = lambda anime_id: {10: anime}[anime_id]

        dashboard = await use_case.execute(
            HighlightDashboardQuery(
                user_id=1,
                emotion="funny",
                category="драма",
                query="joke",
                include_spoilers=False,
                sort_by="popular",
            )
        )

        assert len(dashboard.items) == 2
        assert dashboard.items[0].anime_title == "Initial D"
        assert dashboard.items[0].watch_url == "/watch/185?episode=3&start_at=5"
        assert dashboard.stats.total_highlights == 2
        assert dashboard.stats.top_anime_title == "Initial D"
        assert dashboard.stats.average_duration_seconds == 10.0
        assert dashboard.emotions == ["funny"]
        assert dashboard.categories == ["драма"]
        assert dashboard.selected_sort == "popular"

    async def test_uses_fallback_title_when_anime_missing(self):
        """Что тестируем: запасной заголовок карточки при отсутствии аниме.
        Что передаём: клиент аниме возвращает None.
        Что ожидаем: заголовок вида «Anime #id», ссылка на просмотр по внутреннему id.
        """
        highlight = _highlight(
            episode=1, start_timestamp=1.0, end_timestamp=2.0, title="", anime_id=99
        )
        highlight.id = 5
        use_case, _uow, _repository, _users, _client = _use_case([highlight], anime=None)

        dashboard = await use_case.execute(HighlightDashboardQuery(user_id=1))

        assert dashboard.items[0].anime_title == "Anime #99"
        assert dashboard.items[0].watch_url == "/watch/99?episode=1&start_at=1"
        assert dashboard.selected_sort == "recent"

    async def test_attaches_owner_and_engagement(self):
        """Что тестируем: подстановку автора и социальных метрик в карточку.
        Что передаём: автора списка и вовлечённость зрителя.
        Что ожидаем: имя автора и отметки лайка/сохранения в карточке.
        """
        highlight = _highlight()
        highlight.id = 7
        owner = SimpleNamespace(id=1, username="author", avatar_url="https://example.com/a.png")
        engagement = {7: HighlightEngagement(comments_count=2, is_liked=True, is_saved=False)}
        use_case, _uow, _repository, users, _client = _use_case(
            [highlight], engagement=engagement, users=[owner]
        )

        dashboard = await use_case.execute(HighlightDashboardQuery(user_id=1, viewer_user_id=2))

        users.get_by_ids.assert_awaited_once_with([1])
        card = dashboard.items[0]
        assert card.owner_username == "author"
        assert card.owner_profile_url == "/users/1"
        assert card.comments_count == 2
        assert card.is_liked is True
        assert card.is_saved is False

    async def test_hides_spoilers_and_skips_query_without_owner(self):
        """Что тестируем: фильтр спойлеров и отсутствие владельца в запросе.
        Что передаём: хайлайт-спойлер без запроса, затем запрос без user_id.
        Что ожидаем: спойлер отброшен, пустой дашборд без обращения к репозиторию.
        """
        spoiler = _highlight(is_spoiler=True)
        spoiler.id = 7
        use_case, _uow, repository, _users, _client = _use_case([spoiler])

        dashboard = await use_case.execute(HighlightDashboardQuery(user_id=1))
        empty = await use_case.execute(HighlightDashboardQuery())

        assert dashboard.items == []
        assert empty.items == []
        repository.get_by_user.assert_awaited_once_with(1)
