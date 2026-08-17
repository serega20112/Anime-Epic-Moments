"""Request mappers for recommendation commands."""

from __future__ import annotations

from typing import Any

from backend.application.dto import AskAiRecommendationsCommand

_ASK_LIMIT_DEFAULT = 6
_ASK_LIMIT_MIN = 1
_ASK_LIMIT_MAX = 10


async def map_ask_ai_command(
    payload: dict[str, Any] | None, *, user_id: int
) -> AskAiRecommendationsCommand:
    """Build an ask AI command from a JSON payload.

    The query value is normalized (trimmed) here but empty/invalid queries are
    rejected inside the use case, which owns the validation.

    Args:
        payload: Decoded JSON payload.
        user_id: Acting user identifier.

    Returns:
        AskAiRecommendationsCommand: Command with clamped limit.
    """
    query = str((payload or {}).get("query") or "").strip()
    limit = await _clamp_limit(await _to_int((payload or {}).get("limit")), default=_ASK_LIMIT_DEFAULT)
    return AskAiRecommendationsCommand(
        user_id=user_id,
        query=query,
        limit=limit,
    )


async def _clamp_limit(value: int | None, *, default: int) -> int:
    """Clamp a limit to the allowed range.

    Args:
        value: Parsed value or None when invalid.
        default: Default returned when the value is None.

    Returns:
        int: Clamped limit within allowed bounds.
    """
    if value is None:
        return default
    return max(_ASK_LIMIT_MIN, min(value, _ASK_LIMIT_MAX))


async def _to_int(value: Any) -> int | None:
    """Convert a value to an int, returning None on failure.

    Args:
        value: Raw value from the payload.

    Returns:
        int | None: Parsed integer or None.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
