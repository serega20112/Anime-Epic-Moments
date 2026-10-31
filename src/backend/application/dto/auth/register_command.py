"""Регистрация пользователя с подтверждением адреса почты."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegisterCommand:
    """Команда регистрации с запросом кода подтверждения.

    Attributes:
        email: Нормализованный адрес почты.
        password: Пароль в открытом виде.
        username: Отображаемое имя пользователя.
        theme: Выбранная тема оформления.
    """

    email: str
    password: str
    username: str
    theme: str
