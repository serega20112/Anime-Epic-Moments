"""Abstract token blocklist interface for the domain layer."""

from __future__ import annotations

from abc import ABC, abstractmethod


class TokenBlocklistInterface(ABC):
    """Interface for revoking and checking single-use JWT tokens."""

    @abstractmethod
    async def revoke(self, token: str, ttl_seconds: int) -> None:
        """Mark a token as revoked for the given TTL.

        Args:
            token: Token to revoke.
            ttl_seconds: TTL of the blocklist entry.
        """

    @abstractmethod
    async def consume(self, token: str, ttl_seconds: int) -> bool:
        """Atomically revoke a token unless it was already revoked.

        Only one concurrent caller receives True.

        Args:
            token: Token to consume.
            ttl_seconds: TTL of the blocklist entry.

        Returns:
            bool: True if this call revoked the token, False if already revoked.
        """

    @abstractmethod
    async def is_revoked(self, token: str) -> bool:
        """Check whether a token is currently revoked.

        Args:
            token: Token to check.

        Returns:
            bool: True if the token is revoked.
        """
