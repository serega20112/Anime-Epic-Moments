"""Request mappers for support commands."""

from __future__ import annotations

from typing import Any

from backend.application.dto import CreateSupportTicketCommand
from backend.domain import normalize_support_channel
from backend.domain.policies.user_credentials_policy import normalize_email, normalize_username


async def map_create_support_ticket_command(
    form: dict[str, Any],
    *,
    user_id: int | None,
    user_email: str | None = None,
    user_username: str | None = None,
) -> CreateSupportTicketCommand:
    """Build a create support ticket command from form data.

    Args:
        form: Form data dictionary.
        user_id: Optional authenticated user identifier.
        user_email: Authenticated user email (falls back to form email).
        user_username: Authenticated user username (falls back to form username).

    Returns:
        CreateSupportTicketCommand: Command (validation happens in the use case).
    """
    email = await _normalize_email(user_email if user_id is not None else form.get("email"))
    username = await _normalize_username(
        user_username if user_id is not None else form.get("username")
    )
    subject = str(form.get("subject") or "").strip()
    message = str(form.get("message") or "").strip()
    channel = await normalize_support_channel(form.get("channel"))
    page_url = await _normalize_page_url(form.get("page_url"))
    return CreateSupportTicketCommand(
        user_id=user_id,
        email=email,
        username=username,
        subject=subject,
        message=message,
        channel=channel,
        page_url=page_url,
    )


async def _normalize_email(value: str | None) -> str:
    """Normalize an email address.

    Args:
        value: Raw email string.

    Returns:
        str: Normalized email.
    """
    return await normalize_email(value)


async def _normalize_username(value: str | None) -> str:
    """Normalize a username by collapsing whitespace.

    Args:
        value: Raw username string.

    Returns:
        str: Normalized username.
    """
    return await normalize_username(value)


async def _normalize_page_url(value: str | None) -> str | None:
    """Normalize a page URL.

    Args:
        value: Raw page URL string.

    Returns:
        str | None: Normalized page URL or None.
    """
    normalized = str(value or "").strip()
    return normalized or None
