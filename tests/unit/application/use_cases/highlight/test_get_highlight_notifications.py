from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.highlight.get_highlight_notifications import (
    GetHighlightNotificationsUseCase,
)


@pytest.mark.unit
class TestGetHighlightNotificationsUseCase:
    """Юнит-тесты получения уведомлений по реакциям на хайлайты."""

    @pytest.mark.parametrize(
        ("limit", "expected"),
        [(1, 1), (500, 100), (20, 20)],
    )
    async def test_clamps_limit(self, limit, expected):
        """Что тестируем: ограничение размера выборки уведомлений.
        Что передаём: разные значения limit.
        Что ожидаем: репозиторий вызывается с зажатым limit.
        """
        repo = AsyncMock()
        repo.get_recent_activity.return_value = ["notification"]
        use_case = GetHighlightNotificationsUseCase(repo)

        result = await use_case.execute(user_id=8, limit=limit)

        assert repo.get_recent_activity.await_args.kwargs == {"user_id": 8, "limit": expected}
        assert result == ["notification"]
