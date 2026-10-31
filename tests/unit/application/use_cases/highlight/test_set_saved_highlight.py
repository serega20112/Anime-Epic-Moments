from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import SetSavedHighlightCommand
from backend.application.use_cases.highlight.social.set_saved_highlight import (
    SetSavedHighlightUseCase,
)
from tests.support.fakes import FakeUnitOfWork


def _use_case(repository: AsyncMock) -> tuple:
    """Собрать сценарий сохранения с двойниками репозитория и кэша профиля."""
    profile_cache = AsyncMock()
    uow = FakeUnitOfWork(HighlightRepository=repository)
    use_case = SetSavedHighlightUseCase(uow, profile_cache)
    return use_case, uow, profile_cache


@pytest.mark.unit
class TestSetSavedHighlightUseCase:
    """Юнит-тесты сохранения/снятия с сохранения хайлайта."""

    async def test_delegates_to_repository(self):
        """Что тестируем: делегирование сохранения в репозиторий и инвалидацию профиля.
        Что передаём: существующий хайлайт и команду saved.
        Что ожидаем: отметка сохранена, профиль очищен, результат успешен.
        """
        repository = AsyncMock()
        repository.get_by_id.return_value = SimpleNamespace(user_id=8)
        repository.set_saved.return_value = True
        use_case, uow, profile_cache = _use_case(repository)

        result = await use_case.execute(
            SetSavedHighlightCommand(highlight_id=4, user_id=3, saved=True)
        )

        assert result.ok is True
        assert result.data is True
        assert uow.commits == 1
        repository.set_saved.assert_awaited_once_with(highlight_id=4, user_id=3, saved=True)
        profile_cache.invalidate_user.assert_awaited_once_with(3)

    async def test_returns_failure_for_missing_item(self):
        """Что тестируем: отказ при отсутствующем хайлайте.
        Что передаём: get_by_id=None.
        Что ожидаем: статус 404, отметка не изменяется, профиль не трогается.
        """
        repository = AsyncMock()
        repository.get_by_id.return_value = None
        use_case, _uow, profile_cache = _use_case(repository)

        result = await use_case.execute(
            SetSavedHighlightCommand(highlight_id=999, user_id=3, saved=True)
        )

        assert result.ok is False
        assert result.status_code == 404
        repository.set_saved.assert_not_awaited()
        profile_cache.invalidate_user.assert_not_awaited()
