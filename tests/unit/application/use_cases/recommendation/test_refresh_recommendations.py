from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import RecommendationsQuery
from backend.application.use_cases.recommendation.refresh_recommendations import (
    RefreshRecommendationsUseCase,
)
from tests.support.fakes import FakeUnitOfWork


@pytest.mark.unit
class TestRefreshRecommendationsUseCase:
    """Юнит-тесты обновления рекомендаций."""

    @pytest.mark.parametrize("limit", [3, 5])
    async def test_bypasses_cache(self, limit):
        """Что тестируем: вызов generate с force_refresh=True.
        Что передаём: query-объект с user_id/limit, uow-двойник и замоканный сервис.
        Что ожидаем: результат сервиса возвращается, force_refresh=True.
        """
        service = AsyncMock()
        service.generate.return_value = ["fresh"]
        uow = FakeUnitOfWork()
        use_case = RefreshRecommendationsUseCase(uow, service)

        result = await use_case.execute(RecommendationsQuery(user_id=4, limit=limit))

        assert result == ["fresh"]
        service.generate.assert_awaited_once_with(uow, 4, limit, force_refresh=True)
