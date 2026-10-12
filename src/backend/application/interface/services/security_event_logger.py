"""Security audit event port."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SecurityEventLoggerInterface(ABC):
    """Record security audit events emitted by the application layer."""

    @abstractmethod
    async def log(
        self,
        *,
        event: str,
        user_id: str | int | None = None,
        email: str | None = None,
        ip_address: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Record a security audit event."""
