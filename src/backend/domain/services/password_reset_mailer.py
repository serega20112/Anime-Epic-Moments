"""Abstract password reset mailer interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordResetMailerInterface(ABC):
    """Interface for sending password reset emails."""

    @abstractmethod
    async def send_reset_email(self, email: str, reset_url: str) -> None:
        """Send a password reset email.

        Args:
            email: Recipient email.
            reset_url: Password reset URL.
        """
