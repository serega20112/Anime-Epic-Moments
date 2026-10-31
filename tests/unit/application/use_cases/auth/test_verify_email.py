from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import VerifyEmailCommand
from backend.application.use_cases.auth.verification.verify_email import VerifyEmailUseCase
from tests.support.fakes import FakeUnitOfWork

EMAIL = "user@example.com"


def _payload(**overrides) -> SimpleNamespace:
    """Собрать ожидающую регистрацию с новым кодом подтверждения."""
    fields = {
        "email": EMAIL,
        "username": "tester",
        "password_hash": "hashed",
        "code": "123456",
        "theme": "neon",
    }
    fields.update(overrides)
    return SimpleNamespace(**fields)


def _command(**overrides) -> VerifyEmailCommand:
    """Собрать команду подтверждения почты."""
    fields = {"email": " User@Example.COM ", "code": "123456"}
    fields.update(overrides)
    return VerifyEmailCommand(**fields)


def _use_case(*, payload, taken: bool = False) -> tuple:
    """Собрать сценарий подтверждения почты с двойниками базы и хранилища."""
    user_repository = AsyncMock()
    user_repository.get_by_email.return_value = object() if taken else None
    user_repository.add.side_effect = lambda user: user
    store = AsyncMock()
    store.get.return_value = payload
    uow = FakeUnitOfWork(UserRepository=user_repository)
    return VerifyEmailUseCase(uow, store), uow, user_repository, store


@pytest.mark.unit
class TestVerifyEmailUseCase:
    """Юнит-тесты подтверждения адреса почты кодом."""

    async def test_creates_user_and_clears_pending_registration(self):
        """Что тестируем: завершение регистрации по верному коду.
        Что передаём: совпадающий код и свободный адрес почты.
        Что ожидаем: пользователь создан, pending-запись удалена, успех с редиректом.
        """
        use_case, uow, users, store = _use_case(payload=_payload())

        result = await use_case.execute(_command())

        assert result.ok is True
        assert result.data.username == "tester"
        assert result.data.email == EMAIL
        assert result.message == "Добро пожаловать, tester!"
        assert result.redirect_endpoint == "index.index"
        assert uow.commits == 1
        users.get_by_email.assert_awaited_once_with(EMAIL)
        store.delete.assert_awaited_once_with(EMAIL)

    async def test_rejects_expired_code(self):
        """Что тестируем: отказ при отсутствии ожидающей регистрации.
        Что передаём: хранилище возвращает None.
        Что ожидаем: отказ с возвратом на страницу подтверждения.
        """
        use_case, _uow, users, store = _use_case(payload=None)

        result = await use_case.execute(_command())

        assert result.ok is False
        assert "истёк" in result.error_message
        assert result.redirect_email == EMAIL
        users.add.assert_not_awaited()
        store.delete.assert_not_awaited()

    async def test_rejects_wrong_code(self):
        """Что тестируем: отказ при несовпадении кода.
        Что передаём: код из другой последовательности цифр.
        Что ожидаем: отказ, пользователь не создан, pending-запись сохранена.
        """
        use_case, _uow, users, store = _use_case(payload=_payload())

        result = await use_case.execute(_command(code="654321"))

        assert result.ok is False
        assert "Неверный код" in result.error_message
        users.add.assert_not_awaited()
        store.delete.assert_not_awaited()

    async def test_rejects_email_taken_while_confirming(self):
        """Что тестируем: отказ, если адрес занят за время ожидания кода.
        Что передаём: верный код и существующего пользователя.
        Что ожидаем: отказ, создание отменено, pending-запись удалена.
        """
        use_case, uow, users, store = _use_case(payload=_payload(), taken=True)

        result = await use_case.execute(_command())

        assert result.ok is False
        assert "уже существует" in result.error_message
        assert uow.commits == 1
        users.add.assert_not_awaited()
        store.delete.assert_awaited_once_with(EMAIL)
