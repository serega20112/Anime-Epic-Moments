from __future__ import annotations

from unittest.mock import Mock

from src.backend.use_case.recommendation.generate_recommendations import (
    GenerateRecommendationsUseCase,
)


def test_generate_recommendations_delegates_to_service():
    """Проверяем, что GenerateRecommendationsUseCase вызывает сервис генерации рекомендаций."""
    service = Mock()
    service.generate.return_value = ["rec-1", "rec-2"]
    use_case = GenerateRecommendationsUseCase(service)

    result = use_case.execute(user_id=7, limit=2)

    assert result == ["rec-1", "rec-2"]
    service.generate.assert_called_once_with(7, 2)
