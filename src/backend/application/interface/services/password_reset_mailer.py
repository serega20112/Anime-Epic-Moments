"""Порт отправки писем для восстановления пароля."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordResetMailerInterface(ABC):
    """Отправка писем со ссылкой восстановления пароля."""

    @abstractmethod
    async def send_reset_email(self, email: str, reset_url: str) -> None:
        """Отправить письмо для восстановления пароля."""
