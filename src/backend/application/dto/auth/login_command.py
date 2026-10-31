"""Данные формы входа."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoginCommand:
    """Данные формы входа.

    Attributes:
        email: Нормализованный адрес почты.
        password: Пароль в открытом виде.
    """

    email: str
    password: str
