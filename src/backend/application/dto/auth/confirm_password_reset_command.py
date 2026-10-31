"""Подтверждение сброса пароля одноразовым токеном."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConfirmPasswordResetCommand:
    """Команда подтверждения сброса пароля.

    Attributes:
        token: Токен из письма для восстановления пароля.
        password: Новый пароль в открытом виде.
    """

    token: str
    password: str
