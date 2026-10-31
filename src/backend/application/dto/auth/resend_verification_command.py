"""Повторная отправка кода подтверждения адреса почты."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResendVerificationCommand:
    """Команда повторной отправки кода подтверждения.

    Attributes:
        email: Нормализованный адрес почты.
    """

    email: str
