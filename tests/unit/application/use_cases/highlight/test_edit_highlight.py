from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import EditHighlightCommand
from backend.application.use_cases.highlight.edit_highlight import EditHighlightUseCase
from backend.domain import Highlight


@pytest.mark.unit
class TestEditHighlightUseCase:
    """Юнит-тесты редактирования хайлайта."""

    async def test_updates_highlight_and_invalidates_cache(self):
        """Что тестируем: обновление полей и инвалидацию зависимых кэшей.
        Что передаём: существующий хайлайт и команду редактирования.
        Что ожидаем: поля обновлены, repo.update вызван, кэши инвалидированы.
        """
        highlight = Highlight(
            user_id=7,
            anime_id=1,
            episode=1,
            start_timestamp=1.0,
            end_timestamp=2.0,
            title="old",
            category="драма",
            description="old desc",
        )
        highlight.id = 1
        repo = AsyncMock()
        repo.get_by_id.return_value = highlight
        repo.update.side_effect = lambda item: item
        recommendation_service = AsyncMock()
        dashboard_cache = AsyncMock()
        use_case = EditHighlightUseCase(repo, AsyncMock(), recommendation_service, dashboard_cache)

        result = await use_case.execute(
            EditHighlightCommand(
                highlight_id=1,
                episode=3,
                start_timestamp=10.0,
                end_timestamp=20.0,
                title="new title",
                category="бой",
                description="new desc",
                is_spoiler=True,
                emotion="hype",
            )
        )

        assert result.ok is True
        assert highlight.episode == 3
        assert highlight.title == "new title"
        assert highlight.category == "бой"
        assert highlight.is_spoiler is True
        repo.update.assert_awaited_once_with(highlight)
        recommendation_service.invalidate_user.assert_awaited_once_with(7)
        dashboard_cache.invalidate_public.assert_awaited_once()
        assert result.data is highlight

    @pytest.mark.parametrize("description", ["мат", "спам"])
    async def test_rejects_blocked_description(self, description):
        """Что тестируем: отказ при запрещенном контенте в title/description.
        Что передаём: description с banned-словом и существующий хайлайт.
        Что ожидаем: результат failure со статусом 400, repo.update не вызывается.
        """
        highlight = Highlight(
            user_id=7,
            anime_id=1,
            episode=1,
            start_timestamp=1.0,
            end_timestamp=2.0,
            title="old",
            description="old desc",
        )
        highlight.id = 1
        repo = AsyncMock()
        repo.get_by_id.return_value = highlight
        use_case = EditHighlightUseCase(repo, AsyncMock(), AsyncMock(), AsyncMock())

        result = await use_case.execute(
            EditHighlightCommand(
                highlight_id=1,
                episode=1,
                start_timestamp=10.0,
                end_timestamp=20.0,
                title="blocked",
                category="драма",
                description=description,
                is_spoiler=False,
            )
        )

        assert result.ok is False
        assert result.status_code == 400
        repo.update.assert_not_awaited()

    async def test_returns_failure_for_missing_item(self):
        """Что тестируем: отказ при отсутствующем хайлайте.
        Что передаём: get_by_id=None.
        Что ожидаем: результат failure со статусом 404, repo.update не вызывается.
        """
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        use_case = EditHighlightUseCase(repo, AsyncMock(), AsyncMock(), AsyncMock())

        result = await use_case.execute(
            EditHighlightCommand(
                highlight_id=999,
                episode=1,
                start_timestamp=10.0,
                end_timestamp=20.0,
                title="t",
                category=None,
                description="d",
                is_spoiler=False,
            )
        )

        assert result.ok is False
        assert result.status_code == 404
        repo.update.assert_not_awaited()
