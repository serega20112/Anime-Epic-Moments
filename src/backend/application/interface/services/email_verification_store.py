"""Abstract email verification store interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmailVerificationStoreInterface(ABC):
    """Interface for storing email verification codes."""

    @abstractmethod
    async def generate_code(self, email: str, password: str, username: str, theme: str) -> str:
        """Generate and store a verification code.

        Args:
            email: User email.
            password: User password.
            username: User username.
            theme: User theme preference.

        Returns:
            str: Generated verification code.
        """

    @abstractmethod
    async def verify_code(self, email: str, code: str) -> dict | None:
        """Verify a code and return stored registration data.

        Args:
            email: User email.
            code: Verification code.

        Returns:
            dict | None: Registration data if valid, None otherwise.
        """

    @abstractmethod
    async def has_pending(self, email: str) -> bool:
        """Check if a pending verification exists.

        Args:
            email: User email.

        Returns:
            bool: True if pending verification exists.
        """
