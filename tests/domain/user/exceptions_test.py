from __future__ import annotations

import pytest

from backend.domain.user.exceptions import InvalidEmailError, InvalidUsernameError


@pytest.mark.parametrize(
    ("exc_type", "message"),
    [
        (InvalidEmailError, "bad email"),
        (InvalidUsernameError, "bad username"),
    ],
)
def test_user_exceptions_are_regular_exceptions(exc_type, message):
    """Проверяем, что пользовательские исключения сохраняют сообщение и наследуются от Exception."""
    error = exc_type(message)

    assert isinstance(error, Exception)
    assert str(error) == message
