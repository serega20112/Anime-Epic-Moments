"""Порт отправки писем с кодом подтверждения адреса почты."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmailVerificationMailerInterface(ABC):
    """Отправка писем подтверждения адреса почты."""

    @abstractmethod
    async def send_verification_email(self, email: str, code: str) -> None:
        """Отправить письмо с кодом подтверждения."""
