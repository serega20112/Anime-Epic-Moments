from __future__ import annotations

from unittest.mock import Mock

import pytest

from backend.application.use_cases import (
    PendingEmailVerificationNotFoundError,
    ResendEmailVerificationUseCase,
)
from backend.domain import PendingEmailVerification


def test_resend_email_verification_rejects_missing_pending_registration():
    """Проверяем, что ResendEmailVerificationUseCase отклоняет повторную отправку без ожидающей регистрации."""
    verification_store = Mock()
    verification_store.get.return_value = None
    use_case = ResendEmailVerificationUseCase(verification_store, Mock())

    with pytest.raises(PendingEmailVerificationNotFoundError):
        use_case.execute("user@example.com")


def test_resend_email_verification_rotates_code_saves_pending_payload_and_sends_email(monkeypatch):
    """Проверяем, что ResendEmailVerificationUseCase перевыпускает код, сохраняет pending-запись и отправляет письмо."""
    verification_store = Mock()
    verification_store.get.return_value = PendingEmailVerification(
        email="user@example.com",
        username="tester",
        password_hash="hashed-password",
        code="111111",
        theme="light",
    )
    verification_store.save.side_effect = lambda payload: payload
    mailer = Mock()
    use_case = ResendEmailVerificationUseCase(verification_store, mailer)
    monkeypatch.setattr(use_case, "_generate_code", lambda: "654321")

    result = use_case.execute(" User@Example.com ")

    assert result == PendingEmailVerification(
        email="user@example.com",
        username="tester",
        password_hash="hashed-password",
        code="654321",
        theme="light",
    )
    verification_store.save.assert_called_once_with(result)
    mailer.send_verification_code.assert_called_once_with(
        "user@example.com",
        "654321",
        theme="light",
    )
