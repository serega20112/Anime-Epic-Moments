"""Shared result types returned by authentication use cases.

Use cases return a :class:`AuthResult` instead of raising domain errors so the
presentation layer stays free of error-handling logic and only reads the
outcome fields to decide the HTTP transition (redirect + flash).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AuthResult:
    """Outcome of an authentication use case.

    Attributes:
        ok: Whether the operation succeeded.
        data: Optional payload produced on success.
        message: Flash message displayed on success.
        error_message: Flash message displayed on failure.
        error_endpoint: Named endpoint for the failure redirect.
        redirect_endpoint: Named endpoint for the success redirect.
        redirect_email: Email to preserve on a redirect to the verify page.
    """

    ok: bool
    data: Any = None
    message: str | None = None
    error_message: str | None = None
    error_endpoint: str | None = None
    redirect_endpoint: str | None = None
    redirect_email: str | None = None

    @classmethod
    async def success(
        cls,
        data: Any = None,
        message: str | None = None,
        redirect_endpoint: str | None = None,
        redirect_email: str | None = None,
    ) -> AuthResult:
        """Build a successful result.

        Args:
            data: Optional payload.
            message: Flash message on success.
            redirect_endpoint: Named endpoint for the redirect.
            redirect_email: Email preserved on a redirect to the verify page.

        Returns:
            AuthResult: Successful result.
        """
        return cls(
            ok=True,
            data=data,
            message=message,
            redirect_endpoint=redirect_endpoint,
            redirect_email=redirect_email,
        )

    @classmethod
    async def failure(
        cls,
        error_message: str,
        error_endpoint: str,
        redirect_email: str | None = None,
    ) -> AuthResult:
        """Build a failure result.

        Args:
            error_message: Message to display.
            error_endpoint: Endpoint to redirect back to.
            redirect_email: Email preserve on the verify redirect.

        Returns:
            AuthResult: Failed result.
        """
        return cls(
            ok=False,
            error_message=error_message,
            error_endpoint=error_endpoint,
            redirect_email=redirect_email,
        )
