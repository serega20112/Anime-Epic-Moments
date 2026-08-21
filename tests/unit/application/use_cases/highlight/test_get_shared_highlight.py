from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.highlight.feed.get_shared_highlight import (
    GetSharedHighlightUseCase,
)


@pytest.mark.unit
class TestGetSharedHighlightUseCase:
    """Юнит-тесты получения публичной карточки хайлайта."""

    async def test_increments_views_and_builds_dashboard(self):
        """Что тестируем: увеличение просмотров и сбор shared-dashboard.
        Что передаём: существующий хайлайт и viewer_user_id.
        Что ожидаем: increment_views вызван, результат успешен.
        """
        highlight = SimpleNamespace(user_id=8)

        class StubShared(GetSharedHighlightUseCase):
            async def _build_dashboard(self, **kwargs):
                return {
                    "highlights": [highlight],
                    "sort_by": "recent",
                    "viewer_user_id": kwargs["viewer_user_id"],
                }

        repo = AsyncMock()
        repo.get_by_id.return_value = highlight
        use_case = StubShared(repo, AsyncMock(), AsyncMock())

        result = await use_case.execute(highlight_id=5, viewer_user_id=3)

        repo.increment_views.assert_awaited_once_with(5)
        assert result.ok is True
        assert result.data["highlights"] == [highlight]
        assert result.data["sort_by"] == "recent"
        assert result.data["viewer_user_id"] == 3

    async def test_returns_failure_for_missing_highlight(self):
        """Что тестируем: отказ при отсутствующем хайлайте.
        Что передаём: get_by_id=None.
        Что ожидаем: результат failure со статусом 404, increment_views не вызывается.
        """
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        use_case = GetSharedHighlightUseCase(repo, AsyncMock(), AsyncMock())

        result = await use_case.execute(highlight_id=999, viewer_user_id=3)

        assert result.ok is False
        assert result.status_code == 404
        repo.increment_views.assert_not_awaited()
