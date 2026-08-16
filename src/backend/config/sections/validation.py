"""Content rate limits and validation bounds."""

from __future__ import annotations

import os


def support_ticket_rate_limit() -> int:
    """Return the support ticket creation rate limit.

    Returns:
        int: Support ticket rate limit.
    """
    return int(os.getenv("SUPPORT_TICKET_RATE_LIMIT", "3"))


def highlight_comment_rate_limit() -> int:
    """Return the highlight comment creation rate limit.

    Returns:
        int: Highlight comment rate limit.
    """
    return int(os.getenv("HIGHLIGHT_COMMENT_RATE_LIMIT", "30"))


def highlight_rate_window_seconds() -> int:
    """Return the highlight rate limit window in seconds.

    Returns:
        int: Highlight rate window.
    """
    return int(os.getenv("HIGHLIGHT_RATE_WINDOW_SECONDS", "60"))


def anime_query_limit_max() -> int:
    """Return the maximum allowed anime query limit.

    Returns:
        int: Maximum anime query limit.
    """
    return int(os.getenv("ANIME_QUERY_LIMIT_MAX", "50"))


def anime_title_max_length() -> int:
    """Return the maximum anime title length.

    Returns:
        int: Maximum title length.
    """
    return int(os.getenv("ANIME_TITLE_MAX_LENGTH", "200"))


def anime_description_max_length() -> int:
    """Return the maximum anime description length.

    Returns:
        int: Maximum description length.
    """
    return int(os.getenv("ANIME_DESCRIPTION_MAX_LENGTH", "500"))


def anime_genre_hint_max_length() -> int:
    """Return the maximum genre hint length.

    Returns:
        int: Maximum genre hint length.
    """
    return int(os.getenv("ANIME_GENRE_HINT_MAX_LENGTH", "80"))


def anime_autocomplete_limit_max() -> int:
    """Return the maximum allowed autocomplete limit.

    Returns:
        int: Maximum autocomplete limit.
    """
    return int(os.getenv("ANIME_AUTOCOMPLETE_LIMIT_MAX", "20"))
