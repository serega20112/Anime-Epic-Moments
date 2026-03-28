from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.backend.use_case.auth.login_user import InvalidCredentialsError, LoginUserUseCase


@pytest.mark.parametrize(
    ("user", "is_valid_password", "should_raise"),
    [
        (SimpleNamespace(password_hash="hash"), True, False),
        (SimpleNamespace(password_hash="hash"), False, True),
        (None, False, True),
    ],
)
def test_login_user_validates_credentials(user, is_valid_password, should_raise):
    """Проверяем, что LoginUserUseCase возвращает пользователя только при валидных учетных данных."""
    user_repo = Mock()
    user_repo.get_by_email.return_value = user
    password_service = Mock()
    password_service.verify_password.return_value = is_valid_password
    use_case = LoginUserUseCase(user_repo, password_service)

    if should_raise:
        with pytest.raises(InvalidCredentialsError):
            use_case.execute("user@example.com", "password")
    else:
        result = use_case.execute("user@example.com", "password")
        assert result is user

