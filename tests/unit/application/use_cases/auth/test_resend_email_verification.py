from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.auth.resend_email_verification import (
    ResendEmailVerificationUseCase,
)
from backend.domain import PendingEmailVerification


@pytest.mark.unit
class TestResendEmailVerification:
    """Юнит-тесты повторной отправки кода подтверждения email."""

    async def test_rejects_missing_pending_registration(self):
        """Что тестируем: отказ при отсутствии ожидающей регистрации.
        Что передаём: verification_store.get возвращает None.
        Что ожидаем: AuthResult.failure без отправки письма.
        """
        verification_store = AsyncMock()
        verification_store.get.return_value = None
        mailer = AsyncMock()
        use_case = ResendEmailVerificationUseCase(verification_store, mailer)

        result = await use_case.execute(email="user@example.com")

        assert result.ok is False
        mailer.send_verification_code.assert_not_awaited()

    async def test_rotates_code_and_sends_email(self, monkeypatch):
        """Что тестируем: перевыпуск кода и отправку нового письма.
        Что передаём: существующую pending-запись.
        Что ожидаем: сохраняется запись с новым кодом, письмо отправлено с новым кодом.
        """
        verification_store = AsyncMock()
        verification_store.get.return_value = PendingEmailVerification(
            email="user@example.com",
            username="tester",
            password_hash="hashed-password",
            code="111111",
            theme="light",
        )
        verification_store.save.side_effect = lambda payload: payload
        mailer = AsyncMock()
        use_case = ResendEmailVerificationUseCase(verification_store, mailer)
        async def _fake_code():
            return "654321"

        monkeypatch.setattr(use_case, "_generate_code", _fake_code)

        result = await use_case.execute(email=" User@Example.com ")

        assert result.ok is True
        assert result.redirect_email == "user@example.com"
        saved_payload = verification_store.save.call_args.args[0]
        assert saved_payload.email == "user@example.com"
        assert saved_payload.code == "654321"
        assert saved_payload.theme == "light"
        mailer.send_verification_code.assert_awaited_with(
            "user@example.com", "654321", theme="light"
        )
