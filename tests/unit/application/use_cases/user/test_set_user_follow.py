from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import SetUserFollowCommand
from backend.application.use_cases.user.set_user_follow import SetUserFollowUseCase
from tests.support.fakes import FakeUnitOfWork


@pytest.mark.unit
class TestSetUserFollowUseCase:
    """Юнит-тесты создания/удаления подписки пользователя."""

    def _use_case(self, user_repo: AsyncMock, profile_cache: AsyncMock) -> SetUserFollowUseCase:
        """Собрать сценарий с двойником транзакции и кэша обзоров."""
        return SetUserFollowUseCase(
            FakeUnitOfWork(UserRepository=user_repo),
            profile_cache,
        )

    @pytest.mark.parametrize(
        ("follow", "expected_method"),
        [
            (True, "follow"),
            (False, "unfollow"),
        ],
    )
    async def test_delegates_to_expected_repository_method(self, follow, expected_method):
        """Что тестируем: вызов follow/unfollow в зависимости от команды.
        Что передаём: существующего target-user и флаг follow.
        Что ожидаем: нужный метод репозитория вызван, результат успешен, кэш инвалидирован.
        """
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = SimpleNamespace(id=7)
        getattr(user_repo, expected_method).return_value = follow
        profile_cache = AsyncMock()
        use_case = self._use_case(user_repo, profile_cache)

        result = await use_case.execute(
            SetUserFollowCommand(follower_user_id=3, followed_user_id=7, follow=follow)
        )

        assert result.ok is True
        assert result.data is follow
        getattr(user_repo, expected_method).assert_awaited_once_with(3, 7)
        profile_cache.invalidate_overview.assert_any_await(3)
        profile_cache.invalidate_overview.assert_any_await(7)

    async def test_keeps_cache_valid_without_changes(self):
        """Что тестируем: инвалидацию кэша только после успешной подписки.
        Что передаём: команду с отсутствующим target-user.
        Что ожидаем: invalidate_overview не вызывается.
        """
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = None
        profile_cache = AsyncMock()
        use_case = self._use_case(user_repo, profile_cache)

        result = await use_case.execute(
            SetUserFollowCommand(follower_user_id=3, followed_user_id=99, follow=True)
        )

        assert result.ok is False
        profile_cache.invalidate_overview.assert_not_awaited()

    async def test_rejects_missing_target_user(self):
        """Что тестируем: отсутствие подписки на несуществующего пользователя.
        Что передаём: get_by_id=None.
        Что ожидаем: результат failure со статусом 404, follow не вызывается.
        """
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = None
        use_case = self._use_case(user_repo, AsyncMock())

        result = await use_case.execute(
            SetUserFollowCommand(follower_user_id=3, followed_user_id=99, follow=True)
        )

        assert result.ok is False
        assert result.status_code == 404
        user_repo.follow.assert_not_awaited()
