"""Подтверждение адреса почты одноразовым кодом."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VerifyEmailCommand:
    """Команда подтверждения адреса почты.

    Attributes:
        email: Нормализованный адрес почты.
        code: Код подтверждения из письма.
    """

    email: str
    code: str
