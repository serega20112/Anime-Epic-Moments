"""Domain rules for support delivery channels."""

from __future__ import annotations

SUPPORT_CHANNELS: frozenset[str] = frozenset({"telegram", "email"})
DEFAULT_SUPPORT_CHANNEL = "telegram"


async def normalize_support_channel(value: str | None, *, default: str = DEFAULT_SUPPORT_CHANNEL) -> str:
    """Normalize and validate a support channel, falling back to a default.

    Args:
        value: Raw channel name.
        default: Channel used when the value is not a known channel.

    Returns:
        str: A known channel ("telegram" or "email").
    """
    normalized = str(value or "").strip().lower()
    if normalized in SUPPORT_CHANNELS:
        return normalized
    return default


async def is_support_channel(value: str | None) -> bool:
    """Return whether a value is a known support channel.

    Args:
        value: Channel name to check.

    Returns:
        bool: True when the channel is supported.
    """
    return str(value or "").strip().lower() in SUPPORT_CHANNELS
