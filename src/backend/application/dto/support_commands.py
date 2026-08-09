"""Data transfer objects for support commands."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateSupportTicketCommand:
    """Create a support ticket payload.

    Attributes:
        user_id: Optional authenticated user identifier.
        email: Contact email.
        username: Contact name or nickname.
        subject: Ticket subject.
        message: Ticket body text.
        channel: Delivery channel ("telegram" or "email").
        page_url: Optional page URL where the issue occurred.
    """

    user_id: int | None
    email: str
    username: str
    subject: str
    message: str
    channel: str
    page_url: str | None = None