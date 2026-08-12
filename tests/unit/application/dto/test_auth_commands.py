from __future__ import annotations

import pytest

from backend.application.dto.auth_commands import (
    ConfirmPasswordResetCommand,
    LoginCommand,
    RegisterCommand,
    RequestPasswordResetCommand,
    ResendVerificationCommand,
    UpdateProfileCommand,
    VerifyEmailCommand,
)


class TestLoginCommand:
    def test_stores_fields(self):
        command = LoginCommand(email="a@b.com", password="secret")
        assert command.email == "a@b.com"
        assert command.password == "secret"

    def test_is_frozen(self):
        command = LoginCommand(email="a@b.com", password="secret")
        with pytest.raises(Exception):
            command.password = "x"


class TestRegisterCommand:
    def test_stores_fields(self):
        command = RegisterCommand(
            email="a@b.com",
            password="secret",
            username="tester",
            theme="dark",
        )
        assert command.theme == "dark"
        assert command.username == "tester"


class TestVerifyEmailCommand:
    def test_stores_fields(self):
        command = VerifyEmailCommand(email="a@b.com", code="123456")
        assert command.email == "a@b.com"
        assert command.code == "123456"


class TestResendVerificationCommand:
    def test_stores_fields(self):
        command = ResendVerificationCommand(email="a@b.com")
        assert command.email == "a@b.com"


class TestRequestPasswordResetCommand:
    def test_stores_fields(self):
        command = RequestPasswordResetCommand(
            email="a@b.com",
            base_url="https://example.com",
        )
        assert command.base_url == "https://example.com"


class TestConfirmPasswordResetCommand:
    def test_stores_fields(self):
        command = ConfirmPasswordResetCommand(token="tok", password="newpass")
        assert command.token == "tok"
        assert command.password == "newpass"


class TestUpdateProfileCommand:
    def test_stores_fields(self):
        command = UpdateProfileCommand(user_id=3, username="new", avatar_url="u.png")
        assert command.user_id == 3
        assert command.username == "new"
        assert command.avatar_url == "u.png"

    def test_avatar_defaults_to_none(self):
        command = UpdateProfileCommand(user_id=3, username="new")
        assert command.avatar_url is None