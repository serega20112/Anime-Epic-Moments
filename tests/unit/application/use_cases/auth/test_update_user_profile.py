from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.auth.update_user_profile import (
    UpdateUserProfileUseCase,
)
from backend.domain import User


@pytest.mark.unit
class TestUpdateUserProfileUseCase:
    """Юнит-тесты обновления имени и аватара пользователя."""

    async def test_returns_failure_when_user_not_found(self):
        """Что тестируем: отказ при отсутствии пользователя.
        Что передаём: get_by_id возвращает None.
        Что ожидаем: AuthResult.failure и update не вызывается.
        """
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = None
        use_case = UpdateUserProfileUseCase(user_repo, AsyncMock())

        result = await use_case.execute(user_id=900, username="NewName", avatar_url="http://a/x.png")

        assert result.ok is False
        assert result.error_endpoint == "auth.profile_page"
        user_repo.update.assert_not_awaited()

    async def test_returns_failure_on_empty_username(self):
        """Что тестируем: отказ при пустом имени после очистки.
        Что передаём: пользователя и имя из пробелов.
        Что ожидаем: failure с указанием на страницу профиля, update не вызывается.
        """
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = self._make_user()
        use_case = UpdateUserProfileUseCase(user_repo, AsyncMock())

        result = await use_case.execute(user_id=1, username="   ", avatar_url=None)

        assert result.ok is False
        user_repo.update.assert_not_awaited()

    @pytest.mark.parametrize(
        ("username", "avatar_url", "expected_avatar"),
        [
            ("NewName", "http://a/x.png", "http://a/x.png"),
            ("Spaced Name", "  http://a/y.png  ", "http://a/y.png"),
            ("NoAvatar", None, None),
        ],
    )
    async def test_updates_profile_and_invalidates_cache(self, username, avatar_url, expected_avatar):
        """Что тестируем: успешное обновление имени и аватара.
        Что передаём: имя, аватар и cache надстройку.
        Что ожидаем: союз-код изменяет поля и возвращает success + инвалидацию кэша.
        """
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = self._make_user()
        user_repo.update.side_effect = lambda user: user
        cache = AsyncMock()
        use_case = UpdateUserProfileUseCase(user_repo, AsyncMock(), cache)

        result = await use_case.execute(user_id=1, username=username, avatar_url=avatar_url)

        assert result.ok is True
        assert result.redirect_endpoint == "auth.profile_page"
        updated = user_repo.update.call_args.args[0]
        assert updated.username == username.strip()
        assert updated.avatar_url == expected_avatar
        cache.invalidate_overview.assert_awaited_with(1)

    def _make_user(self):
        return User(
            email="user@example.com",
            username="tester",
            password_hash="hashed-password",
        )