"""Исключения агрегата пользователя."""

from backend.domain.exceptions import ValidationError


class InvalidEmailError(ValidationError):
    """Ошибка некорректного адреса почты."""


class InvalidUsernameError(ValidationError):
    """Ошибка некорректного имени пользователя."""
