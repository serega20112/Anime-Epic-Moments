"""Request mappers for watch commands."""

from __future__ import annotations

from typing import Any

from backend.application.dto import (
    AddAnimeCommentCommand,
    CompleteEpisodeCommand,
    CreateWatchHighlightCommand,
    SaveViewingSessionCommand,
    SetAnimeCommentLikeCommand,
    UpsertUserAnimeStatusCommand,
    WatchPageQuery,
)


async def map_watch_page_query(request) -> WatchPageQuery:
    """Build a watch page query from request query parameters.

    Args:
        request: Incoming HTTP request.

    Returns:
        WatchPageQuery: Parsed watch page query.
    """
    return WatchPageQuery(
        episode=await _to_int(request.query_params.get("episode")) or 1,
        selected_source_id=await _to_int(request.query_params.get("source_id")),
        preferred_start_seconds=await _safe_float(request.query_params.get("start_at")),
        discussion_sort=(
            str(request.query_params.get("discussion_sort") or "popular").strip().lower()
        ),
    )


async def map_upsert_status_command(
    payload: dict[str, Any] | None,
    *,
    user_id: int,
    anime_id: int,
) -> UpsertUserAnimeStatusCommand:
    """Build an upsert status command from a JSON payload.

    Args:
        payload: Decoded JSON payload.
        user_id: Acting user identifier.
        anime_id: Anime identifier.

    Returns:
        UpsertUserAnimeStatusCommand: Command with the raw status string.
    """
    return UpsertUserAnimeStatusCommand(
        user_id=user_id,
        anime_id=anime_id,
        status=str((payload or {}).get("status") or "").strip(),
    )


async def map_save_session_command(
    payload: dict[str, Any] | None,
    *,
    user_id: int,
    anime_id: int,
) -> SaveViewingSessionCommand:
    """Build a save session command from a JSON payload.

    Args:
        payload: Decoded JSON payload.
        user_id: Acting user identifier.
        anime_id: Anime identifier.

    Returns:
        SaveViewingSessionCommand: Command with parsed fields.
    """
    data = payload or {}
    return SaveViewingSessionCommand(
        user_id=user_id,
        anime_id=anime_id,
        episode=await _to_int(data.get("episode")),
        watch_source_id=await _to_int(data.get("watch_source_id")),
        position_seconds=await _to_float(data.get("position_seconds"), default=0.0),
        volume=await _to_float(data.get("volume"), default=1.0),
        quality_label=str(data.get("quality_label") or "Auto").strip() or "Auto",
        is_paused=await _to_bool(data.get("is_paused")),
    )


async def map_complete_episode_command(
    payload: dict[str, Any] | None,
    *,
    user_id: int,
    anime_id: int,
) -> CompleteEpisodeCommand:
    """Build a complete episode command from a JSON payload.

    Args:
        payload: Decoded JSON payload.
        user_id: Acting user identifier.
        anime_id: Anime identifier.

    Returns:
        CompleteEpisodeCommand: Command with the parsed episode.
    """
    return CompleteEpisodeCommand(
        user_id=user_id,
        anime_id=anime_id,
        episode=await _to_int((payload or {}).get("episode")),
    )


async def map_create_watch_highlight_command(
    payload: dict[str, Any] | None,
    *,
    user_id: int,
    anime_id: int,
) -> CreateWatchHighlightCommand:
    """Build a create watch highlight command from a JSON payload.

    Args:
        payload: Decoded JSON payload.
        user_id: Owner user identifier.
        anime_id: Anime identifier.

    Returns:
        CreateWatchHighlightCommand: Command with parsed fields.
    """
    data = payload or {}
    return CreateWatchHighlightCommand(
        user_id=user_id,
        anime_id=anime_id,
        episode=await _to_int(data.get("episode")),
        title=str(data.get("title") or "").strip(),
        category=await _optional_str(data.get("category")),
        start_timestamp=await _to_float(data.get("start_timestamp")),
        end_timestamp=await _to_float(data.get("end_timestamp")),
        description=str(data.get("description") or "").strip(),
        is_spoiler=await _to_bool(data.get("is_spoiler")),
        emotion=await _optional_str(data.get("emotion")),
        original_title=await _optional_str(data.get("original_title")),
        watch_source_id=await _to_int(data.get("watch_source_id")),
        translation_id=await _to_int(data.get("translation_id")),
    )


async def map_add_anime_comment_command(
    payload: dict[str, Any] | None,
    *,
    anime_id: int,
    user_id: int,
) -> AddAnimeCommentCommand:
    """Build an add anime comment command from a JSON payload.

    Args:
        payload: Decoded JSON payload.
        anime_id: Anime identifier.
        user_id: Author identifier.

    Returns:
        AddAnimeCommentCommand: Command with the content string.
    """
    return AddAnimeCommentCommand(
        anime_id=anime_id,
        user_id=user_id,
        content=str((payload or {}).get("content") or "").strip(),
    )


async def map_set_comment_like_command(
    request,
    *,
    comment_id: int,
    user_id: int,
) -> SetAnimeCommentLikeCommand:
    """Build a set comment like command from the request method.

    Args:
        request: Incoming HTTP request.
        comment_id: Comment identifier.
        user_id: Acting user identifier.

    Returns:
        SetAnimeCommentLikeCommand: Command with liked flag from the method.
    """
    return SetAnimeCommentLikeCommand(
        comment_id=comment_id,
        user_id=user_id,
        liked=request.method == "POST",
    )


async def _optional_str(value: Any) -> str | None:
    """Return a trimmed string or None for missing values.

    Args:
        value: Raw value from the payload.

    Returns:
        str | None: Trimmed string or None.
    """
    if value is None:
        return None
    return str(value).strip() or None


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


async def _safe_float(value: Any) -> float | None:
    """Convert a value to a float, returning None on failure.

    Args:
        value: Raw value.

    Returns:
        float | None: Parsed float or None.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def _to_float(value: Any, *, default: float | None = None) -> float | None:
    """Convert a value to a float, returning the default on failure.

    Args:
        value: Raw value from the payload.
        default: Value returned on failure.

    Returns:
        float | None: Parsed float or default.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


async def _to_bool(value: Any) -> bool:
    """Convert a value to a boolean.

    Args:
        value: Raw value from the payload.

    Returns:
        bool: Parsed boolean.
    """
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}
