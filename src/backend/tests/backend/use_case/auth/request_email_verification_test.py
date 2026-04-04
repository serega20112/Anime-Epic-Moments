from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.backend.domain.user.value_object import PendingEmailVerification
from src.backend.use_case.auth.register_user import EmailAlreadyExistsError
from src.backend.use_case.auth.request_email_verification import (
    RequestEmailVerificationUseCase,
)


def test_request_email_verification_rejects_duplicate_email():
    """Проверяем, что RequestEmailVerificationUseCase не создает pending-регистрацию для уже занятого email."""
    user_repo = Mock()
    user_repo.get_by_email.return_value = object()
    use_case = RequestEmailVerificationUseCase(user_repo, Mock(), Mock(), Mock())

    with pytest.raises(EmailAlreadyExistsError):
        use_case.execute("user@example.com", "password123", "tester")


@pytest.mark.parametrize(
    ("email", "username", "theme", "expected_theme"),
    [
        ("User@Example.COM", "tester", "dark", "dark"),
        ("rose@example.com", "rose-user", "rose", "rose"),
        (" user@example.com ", "  tester  ", "unknown", "neon"),
    ],
)
def test_request_email_verification_hashes_password_saves_pending_payload_and_sends_code(
    monkeypatch,
    email,
    username,
    theme,
    expected_theme,
):
    """Проверяем, что RequestEmailVerificationUseCase нормализует данные, хеширует пароль и отправляет код."""
    user_repo = Mock()
    user_repo.get_by_email.return_value = None
    password_service = Mock()
    password_service.hash_password.return_value = "hashed-password"
    verification_store = Mock()
    verification_store.save.side_effect = lambda payload: payload
    mailer = Mock()
    use_case = RequestEmailVerificationUseCase(
        user_repo,
        password_service,
        verification_store,
        mailer,
    )
    monkeypatch.setattr(use_case, "_generate_code", lambda: "123456")

    result = use_case.execute(email, "password123", username, theme=theme)

    assert result == PendingEmailVerification(
        email="user@example.com",
        username="tester",
        password_hash="hashed-password",
        code="123456",
        theme=expected_theme,
    )
    password_service.hash_password.assert_called_once_with("password123")
    verification_store.save.assert_called_once_with(result)
    mailer.send_verification_code.assert_called_once_with(
        "user@example.com",
        "123456",
        theme=expected_theme,
    )
