from __future__ import annotations

import pytest

from backend.domain.aggregates.user.exceptions import InvalidEmailError, InvalidUsernameError
from backend.domain.aggregates.user.user import User


class TestUserValidation:
    """Юнит-тесты валидации сущности User."""

    @pytest.mark.unit
    @pytest.mark.parametrize("email", ["bad-email", "user@", "@mail.com"])
    async def test_rejects_invalid_email(self, email):
        """Что тестируем: валидацию email в конструкторе User.

        Что передаём: некорректные адреса электронной почты.
        Что ожидаем: выбрасывается InvalidEmailError.
        """
        with pytest.raises(InvalidEmailError):
            User(email=email, username="tester", password_hash="hash")

    @pytest.mark.unit
    @pytest.mark.parametrize("username", ["ab", "x" * 21])
    async def test_rejects_invalid_username_length(self, username):
        """Что тестируем: валидацию длины username в конструкторе User.

        Что передаём: слишком короткий и слишком длинный username.
        Что ожидаем: выбрасывается InvalidUsernameError.
        """
        with pytest.raises(InvalidUsernameError):
            User(email="user@example.com", username=username, password_hash="hash")


class TestUserBehaviour:
    """Юнит-тесты поведения агрегата User."""

    @pytest.mark.unit
    async def test_updates_avatar_and_username(self):
        """Что тестируем: методы update_avatar и change_username.

        Что передаём: допустимый URL аватара и новый корректный username.
        Что ожидаем: avatar_url и username обновляются после валидации.
        """
        user = User(email="user@example.com", username="tester", password_hash="hash")

        user.update_avatar("https://example.com/avatar.png")
        user.change_username("renamed")

        assert user.avatar_url == "https://example.com/avatar.png"
        assert user.username == "renamed"

    @pytest.mark.unit
    async def test_domain_does_not_verify_passwords(self):
        """Что тестируем: у агрегата нет метода проверки пароля.
        Что передаём: имя метода, который выглядел как часть контракта.
        Что ожидаем: атрибута нет — проверка хеша живёт в прикладном слое,
        а заглушка с NotImplementedError только вводила в заблуждение.
        """
        user = User(email="user@example.com", username="tester", password_hash="hash")

        assert not hasattr(user, "check_password")
