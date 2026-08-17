"""Form data builders for the support page."""

from __future__ import annotations

from typing import Any

from backend.application.dto import CreateSupportTicketCommand
from backend.domain import normalize_support_channel

_PAGE_URL_MAX_LENGTH = 500


async def build_support_form_data(
    *,
    command: CreateSupportTicketCommand,
    user_email: str | None = None,
    user_username: str | None = None,
) -> dict[str, str]:
    """Build pre-filled form data from a command for re-display.

    Args:
        command: Command with submitted values.
        user_email: Authenticated user email fallback.
        user_username: Authenticated user username fallback.

    Returns:
        dict[str, str]: Normalized form data for re-rendering.
    """
    return {
        "email": (await _normalize_email(user_email) if user_email else command.email),
        "username": (await _normalize_username(user_username) if user_username else command.username),
        "subject": str(command.subject or "").strip(),
        "message": str(command.message or "").strip(),
        "channel": command.channel,
        "page_url": await _normalize_page_url(command.page_url),
    }


async def build_default_support_form(
    *,
    user_email: str | None = None,
    user_username: str | None = None,
    channel_param: Any = None,
    page_param: Any = None,
) -> dict[str, str]:
    """Build default form data from the current user and query params.

    Args:
        user_email: Authenticated user email.
        user_username: Authenticated user username.
        channel_param: Raw channel query parameter.
        page_param: Raw page query parameter.

    Returns:
        dict[str, str]: Normalized form data.
    """
    return {
        "email": await _normalize_email(user_email),
        "username": await _normalize_username(user_username),
        "subject": "",
        "message": "",
        "channel": await normalize_support_channel(channel_param),
        "page_url": await _normalize_page_url(page_param),
    }


async def _normalize_email(value: str | None) -> str:
    """Normalize an email address.

    Args:
        value: Raw email string.

    Returns:
        str: Normalized email.
    """
    return str(value or "").strip().lower()


async def _normalize_username(value: str | None) -> str:
    """Normalize a username by collapsing whitespace.

    Args:
        value: Raw username string.

    Returns:
        str: Normalized username.
    """
    return " ".join(str(value or "").strip().split())


async def _normalize_page_url(value: Any) -> str:
    """Normalize a page URL, truncating to the allowed length.

    Args:
        value: Raw page URL value.

    Returns:
        str: Normalized page URL.
    """
    return str(value or "").strip()[:_PAGE_URL_MAX_LENGTH]
