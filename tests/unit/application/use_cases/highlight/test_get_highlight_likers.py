from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.highlight.get_highlight_likers import GetHighlightLikersUseCase


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
        Что ожидаем: репозиторий вызывается с зажатым limit.
        """
        repo = AsyncMock()
        repo.get_likers.return_value = ["liker"]
        use_case = GetHighlightLikersUseCase(repo)

        result = await use_case.execute(highlight_id=8, limit=limit)

        assert repo.get_likers.await_args.kwargs == {"highlight_id": 8, "limit": expected}
        assert result == ["liker"]