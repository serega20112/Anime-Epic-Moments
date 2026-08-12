from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from backend.application.use_cases.auth.login_user import LoginUserUseCase


@pytest.mark.unit
class TestLoginUserUseCase:
    """Юнит-тесты сценария входа пользователя через email и пароль."""

    @pytest.mark.parametrize(
        ("credentials", "password_matches", "expected_ok"),
        [
            (SimpleNamespace(username="tester", password_hash="hash"), True, True),
            (SimpleNamespace(username="tester", password_hash="hash"), False, False),
            (None, False, False),
        ],
    )
    async def test_authenticates_only_on_valid_credentials(
            self, credentials, password_matches, expected_ok
    ):
        """Что тестируем: проверку учетных данных в LoginUserUseCase.
        Что передаём: найденного или отсутствующего пользователя и ответ проверки пароля.
        Что ожидаем: AuthResult с ok=True только при валидных данных.
        """
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = credentials
        password_service = Mock()
        password_service.verify_password.return_value = password_matches
        use_case = LoginUserUseCase(user_repo, password_service)

        result = await use_case.execute(email="user@example.com", password="password")

        assert result.ok is expected_ok
        user_repo.get_by_email.assert_awaited_with("user@example.com")

    @pytest.mark.parametrize("is_locked", [True, False])
    async def test_rejects_account_when_lock_service_says_locked(self, is_locked):
        """Что тестируем: blockout-механику при наличии account_lock_service.
        Что передаём: значение is_account_locked.
        Что ожидаем: заблокированный аккаунт не проверяет пароль и возвращает failure.
        """
        user_repo = AsyncMock()
        password_service = Mock()
        lock_service = AsyncMock()
        lock_service.is_account_locked.return_value = (is_locked, None)

        use_case = LoginUserUseCase(user_repo, password_service, lock_service)
        result = await use_case.execute(email="user@example.com", password="password")

        lock_service.is_account_locked.assert_awaited_with("user@example.com")
        if is_locked:
            assert result.ok is False
            password_service.verify_password.assert_not_called()
        else:
            user_repo.get_by_email.assert_awaited()

    async def test_success_result_redirects_to_index_and_welcomes_user(self):
        """Что тестируем: наполнение успешного AuthResult.
        Что передаём: существующего пользователя и корректный пароль.
        Что ожидаем: ok=True, data равен пользователю, redirect_endpoint index.index.
        """
        user = SimpleNamespace(id=1, username="tester", password_hash="hash")
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = user
        password_service = Mock()
        password_service.verify_password.return_value = True
        use_case = LoginUserUseCase(user_repo, password_service)

        result = await use_case.execute(email="user@example.com", password="password")

        assert result.ok is True
        assert result.data is user
        assert result.redirect_endpoint == "index.index"
        assert "tester" in (result.message or "")