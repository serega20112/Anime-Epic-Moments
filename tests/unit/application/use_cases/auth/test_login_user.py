from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import LoginCommand
from backend.application.use_cases.auth.login_register.login_user import (
    LoginUserUseCase,
    welcome_message,
)
from backend.domain import User
from tests.support.fakes import FakeUnitOfWork

EMAIL = "user@example.com"


def _user() -> User:
    """Собрать пользователя с подтверждённым паролем."""
    return User(
        id=7,
        email=EMAIL,
        username="tester",
        password_hash="hashed",
        created_at=datetime(2026, 3, 20),
    )


def _use_case(
    *,
    user: User | None = None,
    password_matches: bool = True,
    is_locked: bool = False,
) -> tuple:
    """Собрать сценарий входа с двойниками репозитория, паролей и блокировки."""
    user_repository = AsyncMock()
    user_repository.get_by_email.return_value = user
    password_service = AsyncMock()
    password_service.verify_password.return_value = password_matches
    lock_service = AsyncMock()
    lock_service.is_account_locked.return_value = (is_locked, None)
    uow = FakeUnitOfWork(UserRepository=user_repository)
    use_case = LoginUserUseCase(uow, password_service, lock_service)
    return use_case, uow, user_repository, password_service, lock_service


@pytest.mark.unit
class TestLoginUserUseCase:
    """Юнит-тесты аутентификации пользователя."""

    async def test_authenticates_with_valid_credentials(self):
        """Что тестируем: успешный вход при верном пароле.
        Что передаём: существующего пользователя и корректную команду.
        Что ожидаем: успех, блокировка сброшена, счётчик попыток не увеличивается.
        """
        use_case, uow, _users, _passwords, lock_service = _use_case(user=_user())

        result = await use_case.execute(LoginCommand(email=EMAIL, password="secret"))

        assert result.ok is True
        assert result.data.username == "tester"
        assert result.message == welcome_message("tester")
        assert result.redirect_endpoint == "index.index"
        assert uow.commits == 1
        lock_service.unlock_account.assert_awaited_once_with(EMAIL)
        lock_service.record_failed_attempt.assert_not_awaited()

    async def test_normalizes_email_before_lookup(self):
        """Что тестируем: нормализацию адреса почты перед поиском.
        Что передаём: команду с заглавными буквами и пробелами.
        Что ожидаем: репозиторий вызван с каноническим адресом.
        """
        use_case, _uow, users, _passwords, _lock = _use_case(user=_user())

        await use_case.execute(LoginCommand(email="  User@Example.COM ", password="secret"))

        users.get_by_email.assert_awaited_once_with(EMAIL)

    @pytest.mark.parametrize("password_matches", [True, False])
    async def test_records_failure_for_unknown_or_wrong_password(self, password_matches):
        """Что тестируем: отказ при отсутствии пользователя или неверном пароле.
        Что передаём: password_matches и пользователя None.
        Что ожидаем: отказ с возвратом на страницу входа, попытка учтена.
        """
        use_case, _uow, _users, passwords, lock_service = _use_case(
            user=None, password_matches=password_matches
        )

        result = await use_case.execute(LoginCommand(email=EMAIL, password="secret"))

        assert result.ok is False
        assert result.error_endpoint == "auth.login_page"
        assert "Неверный email или пароль" in result.error_message
        passwords.verify_password.assert_awaited_once()
        lock_service.record_failed_attempt.assert_awaited_once_with(EMAIL)
        lock_service.unlock_account.assert_not_awaited()

    async def test_checks_dummy_hash_for_unknown_user(self):
        """Что тестируем: защиту от перечисления пользователей через тайминг.
        Что передаём: несуществующего пользователя.
        Что ожидаем: проверка пароля выполнена по запасному хешу.
        """
        use_case, _uow, _users, passwords, _lock = _use_case(user=None)

        await use_case.execute(LoginCommand(email=EMAIL, password="secret"))

        checked_hash = passwords.verify_password.await_args.args[1]
        assert checked_hash != "hashed"

    async def test_rejects_account_when_lock_service_says_locked(self):
        """Что тестируем: отказ полностью заблокированного аккаунта.
        Что передаём: is_account_locked=True.
        Что ожидаем: отказ без обращения к репозиторию пользователей.
        """
        use_case, _uow, users, passwords, _lock = _use_case(user=_user(), is_locked=True)

        result = await use_case.execute(LoginCommand(email=EMAIL, password="secret"))

        assert result.ok is False
        assert "заблокирован" in result.error_message
        users.get_by_email.assert_not_awaited()
        passwords.verify_password.assert_not_awaited()
