from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import HighlightCommentsQuery
from backend.application.use_cases.highlight.social.get_highlight_comments import (
    GetHighlightCommentsUseCase,
)
from tests.support.fakes import FakeUnitOfWork


@pytest.mark.unit
class TestGetHighlightCommentsUseCase:
    """Юнит-тесты получения комментариев к хайлайту."""

    @pytest.mark.parametrize(
        ("limit", "expected"),
        [(1, 1), (500, 100), (12, 12)],
    )
    async def test_clamps_limit(self, limit, expected):
        """Что тестируем: ограничение размера выборки комментариев.
        Что передаём: разные значения limit.
        Что ожидаем: репозиторий вызван с зажатым limit, комментарии возвращены.
        """
        repository = AsyncMock()
        repository.get_comments.return_value = ["comment"]
        use_case = GetHighlightCommentsUseCase(FakeUnitOfWork(HighlightRepository=repository))

        result = await use_case.execute(HighlightCommentsQuery(highlight_id=8, limit=limit))

        repository.get_comments.assert_awaited_once_with(highlight_id=8, limit=expected)
        assert result == ["comment"]
