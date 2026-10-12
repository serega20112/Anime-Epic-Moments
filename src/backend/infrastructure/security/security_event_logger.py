"""Infrastructure adapter for the security audit port."""

from __future__ import annotations

from backend.application.interface.services import SecurityEventLoggerInterface
from backend.utils.logging import log_security_event


class SecurityEventLogger(SecurityEventLoggerInterface):
    """Delegate security audit events to the structured JSON logger."""

    async def log(
        self,
        *,
        event: str,
        user_id: str | int | None = None,
        email: str | None = None,
        ip_address: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Record a security audit event.

        Args:
            event: Security event name.
            user_id: User identifier if available.
            email: User email if available.
            ip_address: Client IP address if available.
            details: Additional structured context.
        """
        await log_security_event(
            event=event,
            user_id=str(user_id) if user_id is not None else None,
            email=email,
            ip_address=ip_address,
            **({"details": details} if details else {}),
        )
