from __future__ import annotations

import pytest

from src.backend.domain.user.entity import User
from src.backend.domain.user.exceptions import InvalidEmailError, InvalidUsernameError


@pytest.mark.parametrize("email", ["bad-email", "user@", "@mail.com"])
def test_user_rejects_invalid_email(email):
    """Проверяем, что User валидирует email при создании агрегата."""
    with pytest.raises(InvalidEmailError):
        User(email=email, username="tester", password_hash="hash")


@pytest.mark.parametrize("username", ["ab", "x" * 21])
def test_user_rejects_invalid_username_length(username):
    """Проверяем, что User валидирует длину username при создании агрегата."""
    with pytest.raises(InvalidUsernameError):
        User(email="user@example.com", username=username, password_hash="hash")


def test_user_updates_avatar_and_username():
    """Проверяем, что User обновляет аватар и username после валидации."""
    user = User(email="user@example.com", username="tester", password_hash="hash")

    user.update_avatar("https://example.com/avatar.png")
    user.change_username("renamed")

    assert user.avatar_url == "https://example.com/avatar.png"
    assert user.username == "renamed"


def test_user_check_password_is_not_supported_in_domain():
    """Проверяем, что проверка пароля вынесена из домена и кидает NotImplementedError."""
    user = User(email="user@example.com", username="tester", password_hash="hash")

    with pytest.raises(NotImplementedError):
        user.check_password("plain-password")
