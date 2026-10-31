from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import AddHighlightCommentCommand
from backend.application.use_cases.highlight.social.add_highlight_comment import (
    AddHighlightCommentUseCase,
)
from tests.support.fakes import FakeUnitOfWork


def _use_case(repository: AsyncMock) -> tuple:
    """Собрать сценарий комментария с двойниками репозитория и кэшей."""
    dashboard_cache = AsyncMock()
    profile_cache = AsyncMock()
    uow = FakeUnitOfWork(HighlightRepository=repository)
    use_case = AddHighlightCommentUseCase(uow, dashboard_cache, profile_cache)
    return use_case, uow, dashboard_cache, profile_cache


@pytest.mark.unit
class TestAddHighlightCommentUseCase:
    """Юнит-тесты добавления комментария к хайлайту."""

    async def test_validates_content_and_invalidates_cache(self):
        """Что тестируем: сохранение комментария и инвалидацию кэшей.
        Что передаём: существующий хайлайт и валидный контент.
        Что ожидаем: комментарий сохранён, кэши очищены, результат успешен.
        """
        repository = AsyncMock()
        repository.get_by_id.return_value = SimpleNamespace(user_id=7)
        repository.add_comment.return_value = SimpleNamespace(id=1)
        use_case, uow, dashboard_cache, profile_cache = _use_case(repository)

        result = await use_case.execute(
            AddHighlightCommentCommand(highlight_id=5, user_id=7, content="great scene")
        )

        assert result.ok is True
        assert result.status_code == 201
        assert uow.commits == 1
        repository.add_comment.assert_awaited_once_with(
            highlight_id=5, user_id=7, content="great scene"
        )
        dashboard_cache.invalidate_public.assert_awaited_once()
        profile_cache.invalidate_user.assert_awaited_once_with(7)

    async def test_rejects_empty_content(self):
        """Что тестируем: отказ при пустом комментарии.
        Что передаём: контент из пробелов.
        Что ожидаем: статус 400, комментарий не сохраняется.
        """
        repository = AsyncMock()
        use_case, _uow, dashboard_cache, _profile_cache = _use_case(repository)

        result = await use_case.execute(
            AddHighlightCommentCommand(highlight_id=5, user_id=7, content="   ")
        )

        assert result.ok is False
        assert result.status_code == 400
        repository.add_comment.assert_not_awaited()
        dashboard_cache.invalidate_public.assert_not_awaited()

    async def test_rejects_overlong_content(self):
        """Что тестируем: отказ при слишком длинном комментарии.
        Что передаём: текст длиной 601 символ.
        Что ожидаем: статус 400, комментарий не сохраняется.
        """
        repository = AsyncMock()
        use_case, _uow, _dashboard_cache, _profile_cache = _use_case(repository)

        result = await use_case.execute(
            AddHighlightCommentCommand(highlight_id=5, user_id=7, content="a" * 601)
        )

        assert result.ok is False
        assert result.status_code == 400
        repository.add_comment.assert_not_awaited()

    async def test_returns_not_found_when_highlight_missing(self):
        """Что тестируем: обработку отсутствующего хайлайта.
        Что передаём: get_by_id=None.
        Что ожидаем: статус 404, комментарий не сохраняется.
        """
        repository = AsyncMock()
        repository.get_by_id.return_value = None
        use_case, _uow, dashboard_cache, profile_cache = _use_case(repository)

        result = await use_case.execute(
            AddHighlightCommentCommand(highlight_id=999, user_id=7, content="nice")
        )

        assert result.ok is False
        assert result.status_code == 404
        repository.add_comment.assert_not_awaited()
        dashboard_cache.invalidate_public.assert_not_awaited()
        profile_cache.invalidate_user.assert_not_awaited()
