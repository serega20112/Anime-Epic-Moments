"""Redirect responses for the watch feature."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import RedirectResponse


def discussion_redirect(request: Request, anime_id: int, payload) -> RedirectResponse:
    """Build a redirect back to the watch page after adding a comment.

    Args:
        request: Incoming HTTP request.
        anime_id: Anime ID.
        payload: Request payload with episode and sort.

    Returns:
        RedirectResponse: SEE_OTHER redirect to the watch page.
    """
    episode = _to_int(str((payload or {}).get("episode") or "") or "1")
    discussion_sort = str((payload or {}).get("discussion_sort") or "popular")
    return RedirectResponse(
        url=(
            f"{request.app.url_path_for('watch.watch_page', anime_id=str(anime_id))}"
            f"?episode={episode}"
            f"&discussion_sort={discussion_sort}"
        ),
        status_code=303,
    )


def _to_int(value) -> int:
    """Convert a value to an int, defaulting to 1.

    Args:
        value: Raw string value.

    Returns:
        int: Parsed integer, or 1 when unparseable.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return 1