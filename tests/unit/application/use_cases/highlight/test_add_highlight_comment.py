from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import AddHighlightCommentCommand
from backend.application.use_cases.highlight.add_highlight_comment import AddHighlightCommentUseCase


@pytest.mark.unit
class TestAddHighlightCommentUseCase:
    """Юнит-тесты добавления комментария к хайлайту."""

    async def test_validates_content_and_invalidates_cache(self):
        """Что тестируем: сохранение комментария и инвалидацию публичного кэша.
        Что передаём: существующий хайлайт и валидный контент.
        Что ожидаем: add_comment вызван, кэш инвалидирован, результат успешен.
        """
        repo = AsyncMock()
        repo.get_by_id.return_value = SimpleNamespace(user_id=7)
        repo.add_comment.return_value = SimpleNamespace(id=1)
        dashboard_cache = AsyncMock()
        use_case = AddHighlightCommentUseCase(repo, AsyncMock(), dashboard_cache)

        result = await use_case.execute(
            AddHighlightCommentCommand(
                highlight_id=5, user_id=7, content="great scene"
            )
        )

        assert result.ok is True
        assert result.status_code == 201
        repo.add_comment.assert_awaited_once_with(
            highlight_id=5, user_id=7, content="great scene"
        )
        dashboard_cache.invalidate_public.assert_awaited_once()

    async def test_rejects_empty_content(self):
        """Что тестируем: отказ при пустом комментарии.
        Что передаём: контент из пробелов.
        Что ожидаем: результат failure со статусом 400, add_comment не вызывается.
        """
        repo = AsyncMock()
        use_case = AddHighlightCommentUseCase(repo, AsyncMock())

        result = await use_case.execute(
            AddHighlightCommentCommand(highlight_id=5, user_id=7, content="   ")
        )

        assert result.ok is False
        assert result.status_code == 400
        repo.add_comment.assert_not_awaited()

    async def test_returns_not_found_when_highlight_missing(self):
        """Что тестируем: обработку отсутствующего хайлайта.
        Что передаём: get_by_id=None.
        Что ожидаем: результат failure со статусом 404, add_comment не вызывается.
        """
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        use_case = AddHighlightCommentUseCase(repo, AsyncMock())

        result = await use_case.execute(
            AddHighlightCommentCommand(highlight_id=999, user_id=7, content="nice")
        )

        assert result.ok is False
        assert result.status_code == 404
        repo.add_comment.assert_not_awaited()