from __future__ import annotations

import pytest

from backend.domain.user.exceptions import InvalidEmailError, InvalidUsernameError


class TestUserExceptions:
    """Юнит-тесты пользовательских исключений."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("exc_type", "message"),
        [
            (InvalidEmailError, "bad email"),
            (InvalidUsernameError, "bad username"),
        ],
    )
    def test_are_regular_exceptions(self, exc_type, message):
        """Что тестируем: свойства пользовательских исключений.

        Что передаём: исключение конкретного типа и сообщение об ошибке.
        Что ожидаем: исключение наследуется от Exception и сохраняет сообщение.
        """
        error = exc_type(message)

        assert isinstance(error, Exception)
        assert str(error) == message
