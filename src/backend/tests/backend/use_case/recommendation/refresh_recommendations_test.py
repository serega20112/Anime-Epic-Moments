from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.backend.use_case.recommendation.refresh_recommendations import (
    RefreshRecommendationsUseCase,
)


@pytest.mark.parametrize("limit", [3, 5])
def test_refresh_recommendations_use_case_bypasses_cache(limit):
    """Проверяем, что refresh_recommendations всегда вызывает generate с force_refresh=True."""
    service = Mock()
    service.generate.return_value = ["fresh"]
    use_case = RefreshRecommendationsUseCase(service)

    result = use_case.execute(user_id=4, limit=limit)

    assert result == ["fresh"]
    service.generate.assert_called_once_with(4, limit, force_refresh=True)
