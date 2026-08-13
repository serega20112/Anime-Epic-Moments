from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import SetHighlightLikeCommand
from backend.application.use_cases.highlight.set_highlight_like import SetHighlightLikeUseCase


@pytest.mark.unit
class TestSetHighlightLikeUseCase:
    """Юнит-тесты установки/снятия лайка с хайлайта."""

    async def test_updates_like_and_invalidates_cache(self):
        """Что тестируем: переключение лайка и инвалидацию кэшей.
        Что передаём: существующий хайлайт и команду like.
        Что ожидаем: set_like вызван, кэши инвалидированы.
        """
        repo = AsyncMock()
        repo.get_by_id.return_value = SimpleNamespace(user_id=8)
        repo.set_like.return_value = SimpleNamespace(user_id=8)
        dashboard_cache = AsyncMock()
        profile_cache = AsyncMock()
        use_case = SetHighlightLikeUseCase(repo, AsyncMock(), dashboard_cache, profile_cache)

        result = await use_case.execute(
            SetHighlightLikeCommand(highlight_id=4, user_id=3, liked=True)
        )

        assert result.ok is True
        repo.set_like.assert_awaited_once_with(highlight_id=4, user_id=3, liked=True)
        dashboard_cache.invalidate_public.assert_awaited_once()
        profile_cache.invalidate_overview.assert_awaited()
        invalidate_calls = [
            call.kwargs or call.args
            for call in profile_cache.invalidate_overview.await_args_list
        ]
        assert (3,) in invalidate_calls
        assert (8,) in invalidate_calls

    async def test_returns_failure_for_missing_item(self):
        """Что тестируем: отказ при отсутствующем хайлайте.
        Что передаём: get_by_id=None.
        Что ожидаем: результат failure со статусом 404.
        """
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        use_case = SetHighlightLikeUseCase(repo, AsyncMock())

        result = await use_case.execute(
            SetHighlightLikeCommand(highlight_id=999, user_id=3, liked=True)
        )

        assert result.ok is False
        assert result.status_code == 404