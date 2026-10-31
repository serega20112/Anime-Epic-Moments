from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import HighlightSharedQuery
from backend.application.use_cases.highlight.feed.get_shared_highlight import (
    GetSharedHighlightUseCase,
)
from backend.domain import Highlight, HighlightEngagement
from tests.support.fakes import FakeUnitOfWork


def _highlight(**overrides) -> Highlight:
    """Собрать публичный хайлайт с переопределёнными полями."""
    fields = {
        "user_id": 8,
        "anime_id": 10,
        "episode": 2,
        "start_timestamp": 1.0,
        "end_timestamp": 2.0,
        "title": "Эпичный старт",
    }
    fields.update(overrides)
    highlight = Highlight(**fields)
    highlight.id = 5
    return highlight


def _use_case(highlight, *, engagement=None) -> tuple:
    """Собрать сценарий публичной карточки с двойниками зависимостей."""
    highlight_repository = AsyncMock()
    highlight_repository.get_by_id.return_value = highlight
    highlight_repository.get_engagement_map.return_value = engagement or {}
    user_repository = AsyncMock()
    user_repository.get_by_ids.return_value = [
        SimpleNamespace(id=8, username="author", avatar_url="https://example.com/a.png")
    ]
    anime_api_client = AsyncMock()
    anime_api_client.get_by_id.return_value = None
    uow = FakeUnitOfWork(
        HighlightRepository=highlight_repository,
        UserRepository=user_repository,
    )
    use_case = GetSharedHighlightUseCase(uow, anime_api_client)
    return use_case, uow, highlight_repository


@pytest.mark.unit
class TestGetSharedHighlightUseCase:
    """Юнит-тесты получения публичной карточки хайлайта."""

    async def test_increments_views_and_builds_dashboard(self):
        """Что тестируем: увеличение просмотров и сбор shared-дашборда.
        Что передаём: существующий хайлайт и идентификатор зрителя.
        Что ожидаем: счётчик увеличен, карточка собрана с автором и отметками.
        """
        engagement = {5: HighlightEngagement(comments_count=3, is_liked=True, is_saved=False)}
        use_case, uow, repository = _use_case(_highlight(), engagement=engagement)

        result = await use_case.execute(HighlightSharedQuery(highlight_id=5, viewer_user_id=3))

        assert result.ok is True
        assert uow.commits == 1
        repository.increment_views.assert_awaited_once_with(5)
        card = result.data.items[0]
        assert card.id == 5
        assert card.anime_title == "Anime #10"
        assert card.watch_url == "/watch/10?episode=2&start_at=1"
        assert card.owner_username == "author"
        assert card.comments_count == 3
        assert card.is_liked is True

    async def test_shows_spoiler_highlight_on_share_page(self):
        """Что тестируем: показ спойлерного хайлайта по прямой ссылке.
        Что передаём: хайлайт с is_spoiler=True.
        Что ожидаем: карточка в дашборде, спойлеры включены.
        """
        use_case, _uow, _repository = _use_case(_highlight(is_spoiler=True))

        result = await use_case.execute(HighlightSharedQuery(highlight_id=5))

        assert result.ok is True
        assert len(result.data.items) == 1
        assert result.data.include_spoilers is True

    async def test_returns_failure_for_missing_highlight(self):
        """Что тестируем: отказ при отсутствующем хайлайте.
        Что передаём: get_by_id=None.
        Что ожидаем: статус 404, счётчик просмотров не увеличивается.
        """
        use_case, uow, repository = _use_case(None)

        result = await use_case.execute(HighlightSharedQuery(highlight_id=999, viewer_user_id=3))

        assert result.ok is False
        assert result.status_code == 404
        assert uow.commits == 1
        repository.increment_views.assert_not_awaited()
