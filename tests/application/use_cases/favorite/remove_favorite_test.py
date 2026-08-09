from __future__ import annotations

from unittest.mock import Mock

import pytest

from backend.application.use_cases.favorite.remove_favorite import RemoveFavoriteUseCase


@pytest.mark.parametrize("user_id, anime_id", [(1, 2), (7, 15)])
def test_remove_favorite_use_case_removes_item_and_invalidates_cache(user_id, anime_id):
    """Проверяем, что remove_favorite удаляет запись и очищает рекомендации пользователя."""
    repo = Mock()
    recommendation_service = Mock()
    profile_cache = Mock()
    use_case = RemoveFavoriteUseCase(repo, recommendation_service, profile_cache)

    use_case.execute(user_id=user_id, anime_id=anime_id)

    repo.remove.assert_called_once_with(user_id, anime_id)
    recommendation_service.invalidate_user.assert_called_once_with(user_id)
    profile_cache.invalidate_user.assert_called_once_with(user_id, include_ai_summary=True)
