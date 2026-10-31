from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import RecommendationsQuery
from backend.application.use_cases.recommendation.generate_recommendations import (
    GenerateRecommendationsUseCase,
)
from tests.support.fakes import FakeUnitOfWork


@pytest.mark.unit
class TestGenerateRecommendationsUseCase:
    """Юнит-тесты генерации рекомендаций."""

    async def test_delegates_to_service(self):
        """Что тестируем: передачу границы транзакции, user_id и limit в сервис.
        Что передаём: замоканный service.generate, uow-двойник и query-объект.
        Что ожидаем: результат сервиса возвращается, generate вызван с этими аргументами.
        """
        service = AsyncMock()
        service.generate.return_value = ["rec-1", "rec-2"]
        uow = FakeUnitOfWork()
        use_case = GenerateRecommendationsUseCase(uow, service)

        result = await use_case.execute(RecommendationsQuery(user_id=7, limit=2))

        assert result == ["rec-1", "rec-2"]
        service.generate.assert_awaited_once_with(uow, 7, 2)
        assert uow.commits == 1
