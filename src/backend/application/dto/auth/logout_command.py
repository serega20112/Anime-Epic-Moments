"""Выход пользователя с отзывом токенов."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogoutCommand:
    """Команда выхода из сессии.

    Attributes:
        access_token: Значение access-токена из cookie.
        refresh_token: Значение refresh-токена из cookie.
    """

    access_token: str
    refresh_token: str
