from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import SetHighlightLikeCommand
from backend.application.use_cases.highlight.social.set_highlight_like import (
    SetHighlightLikeUseCase,
)
from tests.support.fakes import FakeUnitOfWork


def _use_case(repository: AsyncMock) -> tuple:
    """Собрать сценарий лайка с двойниками репозиториев и кэшей."""
    dashboard_cache = AsyncMock()
    profile_cache = AsyncMock()
    notification_repository = AsyncMock()
    uow = FakeUnitOfWork(
        HighlightRepository=repository,
        NotificationRepository=notification_repository,
    )
    use_case = SetHighlightLikeUseCase(uow, dashboard_cache, profile_cache)
    return use_case, uow, dashboard_cache, profile_cache, notification_repository


@pytest.mark.unit
class TestSetHighlightLikeUseCase:
    """Юнит-тесты установки/снятия лайка с хайлайта."""

    async def test_updates_like_and_invalidates_cache(self):
        """Что тестируем: переключение лайка и инвалидацию кэшей.
        Что передаём: существующий хайлайт чужого автора и команду like.
        Что ожидаем: лайк сохранён, кэши зрителя и автора очищены.
        """
        repository = AsyncMock()
        repository.get_by_id.return_value = SimpleNamespace(user_id=8)
        repository.set_like.return_value = SimpleNamespace(
            user_id=8, likes_count=4, anime_id=11, id=4
        )
        use_case, uow, dashboard_cache, profile_cache, notifications = _use_case(repository)

        result = await use_case.execute(
            SetHighlightLikeCommand(highlight_id=4, user_id=3, liked=True)
        )

        assert result.ok is True
        assert result.data.likes_count == 4
        assert uow.commits == 1
        repository.set_like.assert_awaited_once_with(highlight_id=4, user_id=3, liked=True)
        dashboard_cache.invalidate_public.assert_awaited_once()
        invalidated = [call.args[0] for call in profile_cache.invalidate_overview.await_args_list]
        assert invalidated == [3, 8]
        notifications.add.assert_awaited_once()
        notified = notifications.add.await_args.args[0]
        assert notified.user_id == 8 and notified.actor_user_id == 3

    async def test_skips_author_invalidation_for_own_highlight(self):
        """Что тестируем: отсутствие двойной инвалидации своего хайлайта.
        Что передаём: хайлайт автора 3 и команду от того же пользователя.
        Что ожидаем: обзор профиля очищен один раз.
        """
        repository = AsyncMock()
        repository.get_by_id.return_value = SimpleNamespace(user_id=3)
        repository.set_like.return_value = SimpleNamespace(
            user_id=3, likes_count=1, anime_id=11, id=4
        )
        use_case, _uow, _dashboard_cache, profile_cache, notifications = _use_case(repository)

        result = await use_case.execute(
            SetHighlightLikeCommand(highlight_id=4, user_id=3, liked=True)
        )

        assert result.ok is True
        assert len(profile_cache.invalidate_overview.await_args_list) == 1
        notifications.add.assert_not_awaited()

    async def test_returns_failure_for_missing_item(self):
        """Что тестируем: отказ при отсутствующем хайлайте.
        Что передаём: get_by_id=None.
        Что ожидаем: статус 404, лайк не изменяется, кэши не трогаются.
        """
        repository = AsyncMock()
        repository.get_by_id.return_value = None
        use_case, _uow, dashboard_cache, profile_cache, _notifications = _use_case(repository)

        result = await use_case.execute(
            SetHighlightLikeCommand(highlight_id=999, user_id=3, liked=True)
        )

        assert result.ok is False
        assert result.status_code == 404
        repository.set_like.assert_not_awaited()
        dashboard_cache.invalidate_public.assert_not_awaited()
        profile_cache.invalidate_overview.assert_not_awaited()
