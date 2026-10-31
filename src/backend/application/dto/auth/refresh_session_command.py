"""Продление сессии по refresh-токену."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RefreshSessionCommand:
    """Команда продления сессии.

    Attributes:
        refresh_token: Значение refresh-токена из cookie.
    """

    refresh_token: str
