from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.recommendation.generate_recommendations import (
    GenerateRecommendationsUseCase,
)


@pytest.mark.unit
class TestGenerateRecommendationsUseCase:
    """Юнит-тесты генерации рекомендаций."""

    async def test_delegates_to_service(self):
        """Что тестируем: передачу user_id/limit в сервис генерации.
        Что передаём: замоканный service.generate.
        Что ожидаем: результат сервиса возвращается, generate вызван с аргументами.
        """
        service = AsyncMock()
        service.generate.return_value = ["rec-1", "rec-2"]
        use_case = GenerateRecommendationsUseCase(service)

        result = await use_case.execute(user_id=7, limit=2)

        assert result == ["rec-1", "rec-2"]
        service.generate.assert_awaited_once_with(7, 2)