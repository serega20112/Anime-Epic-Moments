"""Abstract JWT service interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class JWTServiceInterface(ABC):
    """Interface for JWT token creation and verification."""

    @abstractmethod
    def create_access_token(self, user_id: int) -> str:
        """Create an access token for a user.

        Args:
            user_id: The user identifier.

        Returns:
            str: The encoded JWT access token.
        """

    @abstractmethod
    def create_refresh_token(self, user_id: int) -> str:
        """Create a refresh token for a user.

        Args:
            user_id: The user identifier.

        Returns:
            str: The encoded JWT refresh token.
        """

    @abstractmethod
    def decode_token(self, token: str) -> int:
        """Decode an access token and return the user id.

        Args:
            token: The encoded JWT access token.

        Returns:
            int: The user identifier.

        Raises:
            Exception: If the token is invalid or expired.
        """

    @abstractmethod
    def decode_refresh_token(self, token: str) -> int:
        """Decode a refresh token and return the user id.

        Args:
            token: The encoded JWT refresh token.

        Returns:
            int: The user identifier.
        """

    @abstractmethod
    def create_password_reset_token(self, user_id: int, expires_minutes: int) -> str:
        """Create a password reset token.

        Args:
            user_id: The user identifier.
            expires_minutes: Token expiration in minutes.

        Returns:
            str: The encoded JWT password reset token.
        """

    @abstractmethod
    def decode_password_reset_token(self, token: str) -> int:
        """Decode a password reset token and return the user id.

        Args:
            token: The encoded JWT password reset token.

        Returns:
            int: The user identifier.
        """

    @abstractmethod
    def get_token_ttl_seconds(self, token: str, expected_type: str | None = None) -> int:
        """Get remaining TTL of a token in seconds.

        Args:
            token: The encoded JWT token.
            expected_type: Expected token type for validation.

        Returns:
            int: Remaining TTL in seconds.
        """
