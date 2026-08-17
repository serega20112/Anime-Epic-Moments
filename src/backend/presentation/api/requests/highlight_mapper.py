"""Build application-layer command and query DTOs from highlight HTTP requests.

All JSON parsing, normalization and validation live here so that route
handlers stay thin and only orchestrate use case execution.
"""

from __future__ import annotations

from fastapi import Request

from backend.application.dto import (
    AddHighlightCommentCommand,
    CreateHighlightCommand,
    DeleteHighlightCommand,
    EditHighlightCommand,
    HighlightDashboardQuery,
    HighlightFeedQuery,
    HighlightListQuery,
    SetHighlightLikeCommand,
    SetSavedHighlightCommand,
)

TITLE_MAX_LENGTH = 120
DESCRIPTION_MAX_LENGTH = 600


async def map_create_highlight_command(payload, *, user_id: int | None) -> CreateHighlightCommand | None:
    """Build a create highlight command from a JSON payload.

    Args:
        payload: Decoded JSON payload.
        user_id: Owner user identifier or None for guests.

    Returns:
        CreateHighlightCommand | None: Validated command or None on invalid input.
    """
    payload = payload or {}
    anime_id = await _to_int(payload.get("anime_id"))
    episode = await _to_int(payload.get("episode"))
    start_timestamp = await _safe_to_seconds(payload.get("start_timestamp"))
    end_timestamp = await _safe_to_seconds(payload.get("end_timestamp"))
    if anime_id is None or episode is None or start_timestamp is None or end_timestamp is None:
        return None
    return CreateHighlightCommand(
        user_id=await _to_int(payload.get("user_id"), fallback=user_id),
        anime_id=anime_id,
        episode=episode,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        title=await _trim(payload.get("title"), TITLE_MAX_LENGTH),
        category=await _optional(payload.get("category")),
        description=await _trim(payload.get("description"), DESCRIPTION_MAX_LENGTH),
        is_spoiler=await _to_bool(payload.get("is_spoiler"), default=False),
        emotion=await _optional(payload.get("emotion")),
        highlights_this_hour=await _to_int(payload.get("highlights_this_hour")) or 0,
    )


async def map_edit_highlight_command(payload, *, highlight_id: int) -> EditHighlightCommand:
    """Build an edit highlight command from a JSON payload.

    Args:
        payload: Decoded JSON payload.
        highlight_id: Highlight identifier.

    Returns:
        EditHighlightCommand: Validated edit command.
    """
    payload = payload or {}
    return EditHighlightCommand(
        highlight_id=highlight_id,
        episode=await _to_int(payload.get("episode")),
        start_timestamp=await _to_seconds(payload.get("start_timestamp")),
        end_timestamp=await _to_seconds(payload.get("end_timestamp")),
        title=await _trim(payload.get("title"), TITLE_MAX_LENGTH),
        category=await _optional(payload.get("category")),
        description=await _trim(payload.get("description"), DESCRIPTION_MAX_LENGTH),
        is_spoiler=await _to_bool(payload.get("is_spoiler"), default=False),
        emotion=await _optional(payload.get("emotion")),
    )


async def map_delete_highlight_command(*, highlight_id: int) -> DeleteHighlightCommand:
    """Build a delete highlight command.

    Args:
        highlight_id: Highlight identifier.

    Returns:
        DeleteHighlightCommand: Valid delete command.
    """
    return DeleteHighlightCommand(highlight_id=highlight_id)


async def map_set_like_command(
    request: Request, *, highlight_id: int, user_id: int
) -> SetHighlightLikeCommand:
    """Build a set like command from the request method.

    Args:
        request: Incoming HTTP request.
        highlight_id: Highlight identifier.
        user_id: Acting user identifier.

    Returns:
        SetHighlightLikeCommand: Valid command.
    """
    return SetHighlightLikeCommand(
        highlight_id=highlight_id,
        user_id=user_id,
        liked=request.method == "POST",
    )


async def map_set_saved_command(
    request: Request, *, highlight_id: int, user_id: int
) -> SetSavedHighlightCommand:
    """Build a set saved command from the request method.

    Args:
        request: Incoming HTTP request.
        highlight_id: Highlight identifier.
        user_id: Acting user identifier.

    Returns:
        SetSavedHighlightCommand: Valid command.
    """
    return SetSavedHighlightCommand(
        highlight_id=highlight_id,
        user_id=user_id,
        saved=request.method == "POST",
    )


async def map_add_comment_command(
    payload, *, highlight_id: int, user_id: int
) -> AddHighlightCommentCommand:
    """Build an add comment command from a JSON payload.

    Args:
        payload: Decoded JSON payload.
        highlight_id: Highlight identifier.
        user_id: Author identifier.

    Returns:
        AddHighlightCommentCommand: Validated comment command.
    """
    return AddHighlightCommentCommand(
        highlight_id=highlight_id,
        user_id=user_id,
        content=await _trim((payload or {}).get("content"), DESCRIPTION_MAX_LENGTH),
    )


async def map_dashboard_query(
    request: Request,
    *,
    viewer_user_id: int | None,
) -> HighlightDashboardQuery:
    """Build a dashboard query from request query parameters.

    Args:
        request: Incoming HTTP request.
        viewer_user_id: Optional viewer identifier.

    Returns:
        HighlightDashboardQuery: Validated query.
    """
    return HighlightDashboardQuery(
        anime_id=await _to_int(request.query_params.get("anime_id")),
        emotion=await _optional(request.query_params.get("emotion")),
        category=await _optional(request.query_params.get("category")),
        sort_by=await _optional(request.query_params.get("sort")) or "recent",
        created_date=await _optional(request.query_params.get("date")),
        query=await _optional(request.query_params.get("query")),
        include_spoilers=await _to_bool(request.query_params.get("include_spoilers"), default=False),
        limit=await _clamp_int(request.query_params.get("limit"), default=20, minimum=1, maximum=24),
        viewer_user_id=viewer_user_id,
    )


async def map_list_query(request: Request, *, include_spoilers_default: bool) -> HighlightListQuery:
    """Build a saved/liked list query from request query parameters.

    Args:
        request: Incoming HTTP request.
        include_spoilers_default: Default include spoilers value.

    Returns:
        HighlightListQuery: Validated query.
    """
    return HighlightListQuery(
        anime_id=await _to_int(request.query_params.get("anime_id")),
        emotion=await _optional(request.query_params.get("emotion")),
        category=await _optional(request.query_params.get("category")),
        sort_by=await _optional(request.query_params.get("sort")) or "recent",
        created_date=await _optional(request.query_params.get("date")),
        query=await _optional(request.query_params.get("query")),
        include_spoilers=await _to_bool(
            request.query_params.get("include_spoilers"), default=include_spoilers_default
        ),
    )


async def map_feed_query(request: Request, *, viewer_user_id: int | None) -> HighlightFeedQuery:
    """Build a social feed query from request query parameters.

    Args:
        request: Incoming HTTP request.
        viewer_user_id: Optional viewer identifier.

    Returns:
        HighlightFeedQuery: Validated query.
    """
    return HighlightFeedQuery(
        anime_id=await _to_int(request.query_params.get("anime_id")),
        category=await _optional(request.query_params.get("category")),
        include_spoilers=await _to_bool(request.query_params.get("include_spoilers"), default=False),
        limit=await _clamp_int(request.query_params.get("limit"), default=12, minimum=1, maximum=24),
        viewer_user_id=viewer_user_id,
    )


async def _trim(value, max_length: int) -> str:
    return str(value or "").strip()[:max_length]


async def _optional(value) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


async def _to_bool(value, *, default: bool) -> bool:
    if value in (None, ""):
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


async def _to_int(value, *, fallback=None) -> int | None:
    if value in (None, ""):
        return fallback
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


async def _clamp_int(value, *, default: int, minimum: int, maximum: int) -> int:
    parsed = await _to_int(value)
    if parsed is None:
        return default
    return max(min(parsed, maximum), minimum)


async def _to_seconds(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    if ":" in text:
        minutes, seconds = text.split(":", 1)
        return float(int(minutes) * 60 + int(seconds))
    return float(text)


async def _safe_to_seconds(value) -> float | None:
    try:
        return await _to_seconds(value)
    except (TypeError, ValueError):
        return None
