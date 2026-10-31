from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import RequestPasswordResetCommand
from backend.application.policies import PasswordResetPolicy
from backend.application.use_cases.auth.password_reset.request_password_reset import (
    RequestPasswordResetUseCase,
)
from backend.domain import User
from tests.support.fakes import FakeUnitOfWork

POLICY = PasswordResetPolicy(base_url="https://policy.example", expire_minutes=15)


def _user() -> User:
    """Собрать пользователя, которому отправляется ссылка сброса."""
    return User(
        id=7,
        email="user@example.com",
        username="tester",
        password_hash="hashed",
    )


def _use_case(*, user) -> tuple:
    """Собрать сценарий запроса сброса с двойниками базы, JWT и почты."""
    user_repository = AsyncMock()
    user_repository.get_by_email.return_value = user
    jwt_service = AsyncMock()
    jwt_service.create_password_reset_token.return_value = "reset-token"
    mailer = AsyncMock()
    uow = FakeUnitOfWork(UserRepository=user_repository)
    use_case = RequestPasswordResetUseCase(uow, jwt_service, mailer, POLICY)
    return use_case, user_repository, jwt_service, mailer


@pytest.mark.unit
class TestRequestPasswordResetUseCase:
    """Юнит-тесты запроса ссылки восстановления пароля."""

    async def test_builds_reset_link_from_argument(self):
        """Что тестируем: формирование ссылки из переданного базового адреса.
        Что передаём: существующего пользователя и base_url запроса.
        Что ожидаем: письмо отправлено на почту пользователя с токеном в ссылке.
        """
        use_case, _users, jwt_service, mailer = _use_case(user=_user())

        result = await use_case.execute(
            RequestPasswordResetCommand(email="user@example.com", base_url="https://app.example/")
        )

        assert result.ok is True
        assert result.redirect_endpoint == "auth.password_reset_request_page"
        jwt_service.create_password_reset_token.assert_awaited_once_with(
            user_id=7, expires_minutes=15
        )
        mailer.send_reset_email.assert_awaited_once_with(
            "user@example.com", "https://app.example/auth/password-reset/confirm?token=reset-token"
        )

    async def test_falls_back_to_policy_base_url(self):
        """Что тестируем: запасной адрес приложения из политики.
        Что передаём: пустой base_url в команде.
        Что ожидаем: ссылка собрана из адреса политики без завершающего слеша.
        """
        use_case, _users, _jwt, mailer = _use_case(user=_user())

        await use_case.execute(RequestPasswordResetCommand(email="user@example.com", base_url=""))

        assert mailer.send_reset_email.await_args.args[1].startswith(
            "https://policy.example/auth/password-reset/confirm"
        )

    async def test_skips_unknown_user(self):
        """Что тестируем: одинаковый ответ для несуществующего адреса.
        Что передаём: пользователя None.
        Что ожидаем: успех без отправки письма — существование аккаунта не раскрывается.
        """
        use_case, _users, jwt_service, mailer = _use_case(user=None)

        result = await use_case.execute(
            RequestPasswordResetCommand(email="ghost@example.com", base_url="https://app.example")
        )

        assert result.ok is True
        jwt_service.create_password_reset_token.assert_not_awaited()
        mailer.send_reset_email.assert_not_awaited()

    async def test_normalizes_email(self):
        """Что тестируем: нормализацию адреса перед поиском пользователя.
        Что передаём: почту в верхнем регистре с пробелами.
        Что ожидаем: репозиторий вызван с каноническим адресом.
        """
        use_case, users, _jwt, _mailer = _use_case(user=None)

        await use_case.execute(
            RequestPasswordResetCommand(email=" User@Example.COM ", base_url="https://app.example")
        )

        users.get_by_email.assert_awaited_once_with("user@example.com")
