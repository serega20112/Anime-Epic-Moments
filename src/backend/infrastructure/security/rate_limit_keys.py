"""Builders for rate-limit subject keys."""

from __future__ import annotations


def support_ticket_subject(*, ip_address: str, user_id: int | None) -> str:
    """Build a rate-limit subject key for support ticket creation.

    Authenticated users are keyed by user ID, guests by IP only.

    Args:
        ip_address: Client IP address.
        user_id: Optional authenticated user identifier.

    Returns:
        str: Rate-limit subject key.
    """
    if user_id:
        return f"{ip_address}::user::{user_id}"
    return f"{ip_address}::guest"


def watch_anime_subject(*, ip_address: str, anime_id: int | None) -> str:
    """Build a rate-limit subject key scoped to an anime.

    Args:
        ip_address: Client IP address.
        anime_id: Anime identifier.

    Returns:
        str: Rate-limit subject key.
    """
    return f"{ip_address}::{anime_id or 'unknown'}"


def watch_user_subject(*, ip_address: str, user_id: int | None) -> str:
    """Build a rate-limit subject key scoped to the acting user.

    Authenticated users are keyed by user ID, guests by IP only.

    Args:
        ip_address: Client IP address.
        user_id: Optional authenticated user identifier.

    Returns:
        str: Rate-limit subject key.
    """
    if user_id:
        return f"{ip_address}::{user_id}"
    return f"{ip_address}::guest"