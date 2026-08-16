from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.highlight.get_highlight_comments import (
    GetHighlightCommentsUseCase,
)


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
        Что ожидаем: репозиторий вызывается с зажатым limit.
        """
        repo = AsyncMock()
        repo.get_comments.return_value = ["comment"]
        use_case = GetHighlightCommentsUseCase(repo)

        result = await use_case.execute(highlight_id=8, limit=limit)

        assert repo.get_comments.await_args.kwargs == {"highlight_id": 8, "limit": expected}
        assert result == ["comment"]
