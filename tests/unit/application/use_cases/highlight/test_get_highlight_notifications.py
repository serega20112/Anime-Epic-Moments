from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import HighlightNotificationsQuery
from backend.application.use_cases.highlight.social.get_highlight_notifications import (
    GetHighlightNotificationsUseCase,
)
from tests.support.fakes import FakeUnitOfWork


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
        Что ожидаем: репозиторий вызван с зажатым limit, уведомления возвращены.
        """
        repository = AsyncMock()
        repository.get_recent_activity.return_value = ["notification"]
        use_case = GetHighlightNotificationsUseCase(FakeUnitOfWork(HighlightRepository=repository))

        result = await use_case.execute(HighlightNotificationsQuery(user_id=8, limit=limit))

        repository.get_recent_activity.assert_awaited_once_with(user_id=8, limit=expected)
        assert result == ["notification"]
