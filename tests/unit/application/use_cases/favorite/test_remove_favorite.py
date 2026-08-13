from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.favorite.remove_favorite import RemoveFavoriteUseCase


@pytest.mark.unit
class TestRemoveFavoriteUseCase:
    """Юнит-тесты удаления anime из favorites."""

    @pytest.mark.parametrize("user_id, anime_id", [(1, 2), (7, 15)])
    async def test_removes_item_and_invalidates_cache(self, user_id, anime_id):
        """Что тестируем: удаление записи и очистку зависимых кэшей.
        Что передаём: user_id/anime_id и замоканные сервисы инвалидации.
        Что ожидаем: repo.remove и инвалидации вызваны с ожидаемыми аргументами.
        """
        repo = AsyncMock()
        recommendation_service = AsyncMock()
        profile_cache = AsyncMock()
        use_case = RemoveFavoriteUseCase(repo, AsyncMock(), recommendation_service, profile_cache)

        await use_case.execute(user_id=user_id, anime_id=anime_id)

        repo.remove.assert_awaited_once_with(user_id, anime_id)
        recommendation_service.invalidate_user.assert_awaited_once_with(user_id)
        profile_cache.invalidate_user.assert_awaited_once_with(user_id, include_ai_summary=True)