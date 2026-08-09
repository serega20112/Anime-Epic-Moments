"""Abstract email verification mailer interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmailVerificationMailerInterface(ABC):
    """Interface for sending email verification messages."""

    @abstractmethod
    async def send_verification_email(self, email: str, code: str) -> None:
        """Send a verification email with a code.

        Args:
            email: Recipient email.
            code: Verification code.
        """
