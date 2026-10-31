from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import ResendVerificationCommand
from backend.application.use_cases.auth.verification.resend_email_verification import (
    ResendEmailVerificationUseCase,
)


def _payload() -> SimpleNamespace:
    """Собрать ожидающую регистрацию с прежним кодом."""
    return SimpleNamespace(
        email="user@example.com",
        username="tester",
        password_hash="hashed",
        code="111111",
        theme="dark",
    )


def _use_case(*, payload) -> tuple:
    """Собрать сценарий перевыпуска кода с двойниками хранилища и почты."""
    store = AsyncMock()
    store.get.return_value = payload
    mailer = AsyncMock()
    return ResendEmailVerificationUseCase(store, mailer), store, mailer


@pytest.mark.unit
class TestResendEmailVerification:
    """Юнит-тесты повторной отправки кода подтверждения."""

    async def test_rotates_code_and_sends_email(self):
        """Что тестируем: перевыпуск кода с сохранением данных регистрации.
        Что передаём: существующую pending-запись.
        Что ожидаем: новый шестизначный код сохранён и отправлен, прежние поля целы.
        """
        use_case, store, mailer = _use_case(payload=_payload())

        result = await use_case.execute(ResendVerificationCommand(email=" USER@Example.COM "))

        assert result.ok is True
        assert result.data == "user@example.com"
        assert result.redirect_email == "user@example.com"
        stored = store.save.await_args.args[0]
        assert stored.email == "user@example.com"
        assert stored.username == "tester"
        assert stored.password_hash == "hashed"
        assert stored.theme == "dark"
        assert len(stored.code) == 6 and stored.code.isdigit()
        mailer.send_verification_code.assert_awaited_once_with(
            stored.email, stored.code, theme="dark"
        )

    async def test_rejects_missing_pending_registration(self):
        """Что тестируем: отказ при отсутствии ожидающей регистрации.
        Что передаём: хранилище возвращает None.
        Что ожидаем: отказ на страницу подтверждения, письмо не отправляется.
        """
        use_case, store, mailer = _use_case(payload=None)

        result = await use_case.execute(ResendVerificationCommand(email="ghost@example.com"))

        assert result.ok is False
        assert result.error_endpoint == "auth.verify_email_page"
        assert result.redirect_email == "ghost@example.com"
        store.save.assert_not_awaited()
        mailer.send_verification_code.assert_not_awaited()
