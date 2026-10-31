from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import ConfirmPasswordResetCommand
from backend.application.use_cases.auth.password_reset.reset_password import ResetPasswordUseCase
from backend.domain import User
from backend.domain.exceptions import InvalidTokenError
from tests.support.fakes import FakeUnitOfWork

TOKEN = "reset-token"


def _user() -> User:
    """Собрать пользователя, которому принадлежит токен сброса."""
    return User(id=7, email="user@example.com", username="tester", password_hash="old-hash")


def _use_case(
    *,
    user=None,
    decode_error: Exception | None = None,
    consumed: bool = True,
) -> tuple:
    """Собрать сценарий сброса пароля с двойниками всех зависимостей."""
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = user
    user_repository.update_password.return_value = None
    jwt_service = AsyncMock()
    jwt_service.get_token_ttl_seconds.return_value = 300
    if decode_error is not None:
        jwt_service.decode_password_reset_token.side_effect = decode_error
    else:
        jwt_service.decode_password_reset_token.return_value = 7
    password_service = AsyncMock()
    password_service.hash_password.return_value = "new-hash"
    blocklist = AsyncMock()
    blocklist.consume.return_value = consumed
    uow = FakeUnitOfWork(UserRepository=user_repository)
    use_case = ResetPasswordUseCase(uow, jwt_service, password_service, blocklist)
    return use_case, uow, user_repository, jwt_service, password_service, blocklist


@pytest.mark.unit
class TestResetPasswordUseCase:
    """Юнит-тесты сброса пароля по одноразовому токену."""

    async def test_updates_password_and_consumes_token(self):
        """Что тестируем: успешный сброс пароля по валидному токену.
        Что передаём: существующего пользователя и непотреблённый токен.
        Что ожидаем: пароль перезаписан хешем, токен отозван, редирект на вход.
        """
        use_case, uow, users, _jwt, passwords, blocklist = _use_case(user=_user())

        result = await use_case.execute(ConfirmPasswordResetCommand(token=TOKEN, password="new"))

        assert result.ok is True
        assert result.redirect_endpoint == "auth.login_page"
        assert "Пароль обновлен" in result.message
        assert uow.commits == 1
        passwords.hash_password.assert_awaited_once_with("new")
        blocklist.consume.assert_awaited_once_with(TOKEN, 300)
        users.update_password.assert_awaited_once_with(user_id=7, password_hash="new-hash")

    async def test_rejects_blank_token(self):
        """Что тестируем: отказ на пустом токене.
        Что передаём: команду из пробелов.
        Что ожидаем: отказ на страницу подтверждения без разбора токена.
        """
        use_case, _uow, users, jwt_service, _passwords, _blocklist = _use_case(user=_user())

        result = await use_case.execute(ConfirmPasswordResetCommand(token="   ", password="new"))

        assert result.ok is False
        assert result.error_endpoint == "auth.password_reset_confirm_page"
        jwt_service.decode_password_reset_token.assert_not_awaited()
        users.update_password.assert_not_awaited()

    async def test_rejects_invalid_token(self):
        """Что тестируем: отказ на повреждённом или просроченном токене.
        Что передаём: JWT-сервис бросает доменный InvalidTokenError.
        Что ожидаем: отказ, пользователь не читается.
        """
        use_case, _uow, users, _jwt, _passwords, blocklist = _use_case(
            decode_error=InvalidTokenError("expired")
        )

        result = await use_case.execute(ConfirmPasswordResetCommand(token=TOKEN, password="new"))

        assert result.ok is False
        assert "недействительна или устарела" in result.error_message
        users.get_by_id.assert_not_awaited()
        blocklist.consume.assert_not_awaited()

    async def test_rejects_missing_user(self):
        """Что тестируем: отказ, если пользователь удалён из базы.
        Что передаём: валидный токен и отсутствующего пользователя.
        Что ожидаем: отказ, токен не потребляется.
        """
        use_case, _uow, _users, _jwt, _passwords, blocklist = _use_case(user=None)

        result = await use_case.execute(ConfirmPasswordResetCommand(token=TOKEN, password="new"))

        assert result.ok is False
        assert result.error_message == "Пользователь не найден"
        blocklist.consume.assert_not_awaited()

    async def test_rejects_revoked_token(self):
        """Что тестируем: повторное использование ссылки сброса.
        Что передаём: блок-лист отвечает, что токен уже потреблён.
        Что ожидаем: отказ с текстом об использовании, пароль не меняется.
        """
        use_case, _uow, users, _jwt, _passwords, _blocklist = _use_case(
            user=_user(), consumed=False
        )

        result = await use_case.execute(ConfirmPasswordResetCommand(token=TOKEN, password="new"))

        assert result.ok is False
        assert "уже использована" in result.error_message
        users.update_password.assert_not_awaited()
