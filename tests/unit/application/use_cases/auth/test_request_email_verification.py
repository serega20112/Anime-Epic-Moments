from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import RegisterCommand
from backend.application.use_cases.auth.verification.request_email_verification import (
    RequestEmailVerificationUseCase,
)
from tests.support.fakes import FakeUnitOfWork


def _command(**overrides) -> RegisterCommand:
    """Собрать команду регистрации с переопределёнными полями."""
    fields = {
        "email": " User@Example.COM ",
        "password": "secret-password",
        "username": "  tester  ",
        "theme": "unknown",
    }
    fields.update(overrides)
    return RegisterCommand(**fields)


def _use_case(*, taken: bool = False) -> tuple:
    """Собрать сценарий с двойниками репозитория, паролей, хранилища и почты."""
    user_repository = AsyncMock()
    user_repository.get_by_email.return_value = object() if taken else None
    password_service = AsyncMock()
    password_service.hash_password.return_value = "hashed"
    store = AsyncMock()
    mailer = AsyncMock()
    uow = FakeUnitOfWork(UserRepository=user_repository)
    use_case = RequestEmailVerificationUseCase(uow, password_service, store, mailer)
    return use_case, uow, user_repository, password_service, store, mailer


@pytest.mark.unit
class TestRequestEmailVerification:
    """Юнит-тесты запроса кода подтверждения почты."""

    async def test_normalizes_hashes_saves_and_sends_code(self):
        """Что тестируем: нормализацию данных, хеширование и отправку кода.
        Что передаём: почту в верхнем регистре, имя с пробелами и неизвестную тему.
        Что ожидаем: pending-запись с каноническими полями, код из шести цифр.
        """
        use_case, uow, users, passwords, store, mailer = _use_case()

        result = await use_case.execute(_command())

        assert result.ok is True
        assert result.data == "user@example.com"
        assert result.redirect_email == "user@example.com"
        assert result.redirect_endpoint == "auth.verify_email_page"
        assert uow.commits == 1
        users.get_by_email.assert_awaited_once_with("user@example.com")
        passwords.hash_password.assert_awaited_once_with("secret-password")
        payload = store.save.await_args.args[0]
        assert payload.email == "user@example.com"
        assert payload.username == "tester"
        assert payload.theme == "neon"
        assert len(payload.code) == 6 and payload.code.isdigit()
        mailer.send_verification_code.assert_awaited_once_with(
            payload.email, payload.code, theme="neon"
        )

    async def test_keeps_allowed_theme(self):
        """Что тестируем: сохранение допустимой темы оформления.
        Что передаём: theme='rose'.
        Что ожидаем: pending-запись сохраняет выбранную тему.
        """
        use_case, _uow, _users, _passwords, store, _mailer = _use_case()

        await use_case.execute(_command(theme="ROSE"))

        assert store.save.await_args.args[0].theme == "rose"

    async def test_rejects_duplicate_email(self):
        """Что тестируем: отказ при занятом адресе почты.
        Что передаём: репозиторий находит существующего пользователя.
        Что ожидаем: отказ на страницу регистрации, код не отправляется.
        """
        use_case, _uow, _users, _passwords, store, mailer = _use_case(taken=True)

        result = await use_case.execute(_command())

        assert result.ok is False
        assert result.error_endpoint == "auth.register_page"
        assert "уже существует" in result.error_message
        store.save.assert_not_awaited()
        mailer.send_verification_code.assert_not_awaited()
