from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import DeleteHighlightCommand
from backend.application.use_cases.highlight.delete_highlight import DeleteHighlightUseCase
from backend.domain import Highlight


@pytest.mark.unit
class TestDeleteHighlightUseCase:
    """Юнит-тесты удаления хайлайта."""

    async def test_removes_highlight_and_invalidates_cache(self):
        """Что тестируем: удаление найденного хайлайта и очистку рекомендаций.
        Что передаём: существующий хайлайт и сервис инвалидации.
        Что ожидаем: delete вызван, рекомендации очищены, статус 204.
        """
        highlight = Highlight(
            user_id=8,
            anime_id=1,
            episode=1,
            start_timestamp=1.0,
            end_timestamp=2.0,
            description="desc",
        )
        highlight.id = 55
        repo = AsyncMock()
        repo.get_by_id.return_value = highlight
        recommendation_service = AsyncMock()
        use_case = DeleteHighlightUseCase(repo, AsyncMock(), recommendation_service)

        result = await use_case.execute(DeleteHighlightCommand(highlight_id=55))

        assert result.ok is True
        assert result.status_code == 204
        repo.delete.assert_awaited_once_with(55)
        recommendation_service.invalidate_user.assert_awaited_once_with(8)

    @pytest.mark.parametrize("highlight_id", [1, 77])
    async def test_returns_failure_for_missing_item(self, highlight_id):
        """Что тестируем: корректный ответ при отсутствии хайлайта.
        Что передаём: get_by_id=None.
        Что ожидаем: результат failure со статусом 404, delete не вызывается.
        """
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        use_case = DeleteHighlightUseCase(repo, AsyncMock(), AsyncMock())

        result = await use_case.execute(DeleteHighlightCommand(highlight_id=highlight_id))

        assert result.ok is False
        assert result.status_code == 404
        repo.delete.assert_not_awaited()