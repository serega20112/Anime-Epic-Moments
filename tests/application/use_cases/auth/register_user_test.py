from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.application.use_cases import EmailAlreadyExistsError, RegisterUserUseCase


def test_register_user_rejects_duplicate_email():
    """Проверяем, что RegisterUserUseCase не создает пользователя с уже занятым email."""
    user_repo = Mock()
    user_repo.get_by_email.return_value = object()
    use_case = RegisterUserUseCase(user_repo, Mock())

    with pytest.raises(EmailAlreadyExistsError):
        use_case.execute("user@example.com", "password", "tester")


def test_register_user_hashes_password_and_saves_user():
    """Проверяем, что RegisterUserUseCase хеширует пароль и передает пользователя в репозиторий."""
    user_repo = Mock()
    user_repo.get_by_email.return_value = None
    user_repo.add.return_value = SimpleNamespace(id=1, email="user@example.com")
    password_service = Mock()
    password_service.hash_password.return_value = "hashed-password"
    use_case = RegisterUserUseCase(user_repo, password_service)

    result = use_case.execute("user@example.com", "password", "tester")

    assert result.id == 1
    saved_user = user_repo.add.call_args.args[0]
    assert saved_user.email == "user@example.com"
    assert saved_user.username == "tester"
    assert saved_user.password_hash == "hashed-password"
