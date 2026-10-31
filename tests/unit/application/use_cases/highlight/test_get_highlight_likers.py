from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import HighlightLikersQuery
from backend.application.use_cases.highlight.social.get_highlight_likers import (
    GetHighlightLikersUseCase,
)
from tests.support.fakes import FakeUnitOfWork


@pytest.mark.unit
class TestGetHighlightLikersUseCase:
    """Юнит-тесты получения пользователей, лайкнувших хайлайт."""

    @pytest.mark.parametrize(
        ("limit", "expected"),
        [(2, 2), (500, 100), (17, 17)],
    )
    async def test_clamps_limit(self, limit, expected):
        """Что тестируем: ограничение размера выборки лайкнувших.
        Что передаём: разные значения limit.
        Что ожидаем: репозиторий вызван с зажатым limit, список возвращён.
        """
        repository = AsyncMock()
        repository.get_likers.return_value = ["liker"]
        use_case = GetHighlightLikersUseCase(FakeUnitOfWork(HighlightRepository=repository))

        result = await use_case.execute(HighlightLikersQuery(highlight_id=8, limit=limit))

        repository.get_likers.assert_awaited_once_with(highlight_id=8, limit=expected)
        assert result == ["liker"]
