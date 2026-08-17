"""Result type returned by the create support ticket use case.

The use case returns a :class:`CreateSupportTicketResult` instead of raising
domain errors so the presentation layer stays free of error-handling logic and
only reads the outcome fields to flash a message and pick the HTTP transition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CreateSupportTicketResult:
    """Outcome of the create support ticket use case.

    Attributes:
        ok: Whether the ticket was created.
        status_code: HTTP status to return.
        data: Created ticket on success.
        error_message: Flash message displayed on failure.
        message: Flash message displayed on success.
        service_unavailable: Whether delivery failed because the channel is down.
    """

    ok: bool
    status_code: int = 200
    data: Any = None
    error_message: str | None = None
    message: str | None = None
    service_unavailable: bool = False

    @classmethod
    async def success(
        cls,
        data: Any,
        message: str | None = None,
        service_unavailable: bool = False,
    ) -> CreateSupportTicketResult:
        """Build a successful result.

        Args:
            data: Created ticket.
            message: Success flash message.
            service_unavailable: Whether delivery failed due to a down channel.

        Returns:
            CreateSupportTicketResult: Successful result.
        """
        return cls(
            ok=True,
            status_code=200,
            data=data,
            message=message,
            service_unavailable=service_unavailable,
        )

    @classmethod
    async def failure(cls, error_message: str, status_code: int = 400) -> CreateSupportTicketResult:
        """Build a failed result.

        Args:
            error_message: Flash message to display.
            status_code: HTTP status for the response.

        Returns:
            CreateSupportTicketResult: Failed result.
        """
        return cls(ok=False, status_code=status_code, error_message=error_message)
