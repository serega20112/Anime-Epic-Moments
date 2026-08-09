"""Abstract password service interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordServiceInterface(ABC):
    """Interface for password hashing and verification."""

    @abstractmethod
    def hash_password(self, plain_password: str) -> str:
        """Hash a plain password.

        Args:
            plain_password: The plain text password.

        Returns:
            str: The hashed password.
        """

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.

        Args:
            plain_password: The plain text password.
            hashed_password: The stored password hash.

        Returns:
            bool: True if the password matches the hash.
        """
