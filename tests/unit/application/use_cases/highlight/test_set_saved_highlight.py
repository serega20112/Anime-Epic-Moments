from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import SetSavedHighlightCommand
from backend.application.use_cases.highlight.set_saved_highlight import SetSavedHighlightUseCase


@pytest.mark.unit
class TestSetSavedHighlightUseCase:
    """Юнит-тесты сохранения/снятия с сохранения хайлайта."""

    async def test_delegates_to_repository(self):
        """Что тестируем: делегирование сохранения в репозиторий и инвалидацию профиля.
        Что передаём: существующий хайлайт и команду saved.
        Что ожидаем: set_saved вызван, профиль инвалидирован, результат успешен.
        """
        repo = AsyncMock()
        repo.get_by_id.return_value = SimpleNamespace(user_id=8)
        repo.set_saved.return_value = True
        profile_cache = AsyncMock()
        use_case = SetSavedHighlightUseCase(repo, AsyncMock(), profile_cache)

        result = await use_case.execute(
            SetSavedHighlightCommand(highlight_id=4, user_id=3, saved=True)
        )

        assert result.ok is True
        repo.set_saved.assert_awaited_once_with(highlight_id=4, user_id=3, saved=True)
        profile_cache.invalidate_user.assert_awaited_once_with(3)

    async def test_returns_failure_for_missing_item(self):
        """Что тестируем: отказ при отсутствующем хайлайте.
        Что передаём: get_by_id=None.
        Что ожидаем: результат failure со статусом 404.
        """
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        use_case = SetSavedHighlightUseCase(repo, AsyncMock())

        result = await use_case.execute(
            SetSavedHighlightCommand(highlight_id=999, user_id=3, saved=True)
        )

        assert result.ok is False
        assert result.status_code == 404
