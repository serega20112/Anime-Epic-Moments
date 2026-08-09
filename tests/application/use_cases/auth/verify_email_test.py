from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

import pytest

from backend.application.use_cases import EmailAlreadyExistsError
from backend.application.use_cases import (
    EmailVerificationExpiredError,
    InvalidEmailVerificationCodeError,
    VerifyEmailUseCase,
)
from backend.domain import PendingEmailVerification
from backend.domain import User


def test_verify_email_rejects_missing_pending_registration():
    """Проверяем, что VerifyEmailUseCase отклоняет подтверждение без сохраненного pending-кода."""
    user_repo = Mock()
    verification_store = Mock()
    verification_store.get.return_value = None
    use_case = VerifyEmailUseCase(user_repo, verification_store)

    with pytest.raises(EmailVerificationExpiredError):
        use_case.execute("user@example.com", "123456")


def test_verify_email_rejects_invalid_code():
    """Проверяем, что VerifyEmailUseCase отклоняет неверный код подтверждения."""
    user_repo = Mock()
    verification_store = Mock()
    verification_store.get.return_value = PendingEmailVerification(
        email="user@example.com",
        username="tester",
        password_hash="hashed-password",
        code="654321",
        theme="dark",
    )
    use_case = VerifyEmailUseCase(user_repo, verification_store)

    with pytest.raises(InvalidEmailVerificationCodeError):
        use_case.execute("user@example.com", "123456")


def test_verify_email_rejects_existing_user_and_clears_pending_payload():
    """Проверяем, что VerifyEmailUseCase не создает дубликат пользователя и удаляет pending-запись."""
    user_repo = Mock()
    user_repo.get_by_email.return_value = User(
        id=7,
        email="user@example.com",
        username="tester",
        password_hash="hashed-password",
        created_at=datetime(2026, 3, 28),
    )
    verification_store = Mock()
    verification_store.get.return_value = PendingEmailVerification(
        email="user@example.com",
        username="tester",
        password_hash="hashed-password",
        code="123456",
        theme="dark",
    )
    use_case = VerifyEmailUseCase(user_repo, verification_store)

    with pytest.raises(EmailAlreadyExistsError):
        use_case.execute("user@example.com", "123456")

    verification_store.delete.assert_called_once_with("user@example.com")


def test_verify_email_creates_user_and_deletes_pending_payload():
    """Проверяем, что VerifyEmailUseCase создает пользователя после правильного кода и очищает pending-запись."""
    user_repo = Mock()
    user_repo.get_by_email.return_value = None
    user_repo.add.side_effect = lambda user: User(
        id=9,
        email=user.email,
        username=user.username,
        password_hash=user.password_hash,
        created_at=datetime(2026, 3, 28),
    )
    verification_store = Mock()
    verification_store.get.return_value = PendingEmailVerification(
        email="user@example.com",
        username="tester",
        password_hash="hashed-password",
        code="123456",
        theme="dark",
    )
    use_case = VerifyEmailUseCase(user_repo, verification_store)

    result = use_case.execute("User@Example.com", "123456")

    assert result.id == 9
    assert result.email == "user@example.com"
    assert result.username == "tester"
    assert result.password_hash == "hashed-password"
    verification_store.delete.assert_called_once_with("user@example.com")
