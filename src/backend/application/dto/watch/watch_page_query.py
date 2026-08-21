"""Query parameters for building the anime watch page."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WatchPageQuery:
    """Query parameters for building the anime watch page.

    Attributes:
        episode: Requested episode number.
        selected_source_id: Optional pre-selected watch source.
        preferred_start_seconds: Optional playback start offset in seconds.
        discussion_sort: Comment sort key ("popular" or "recent").
    """

    episode: int = 1
    selected_source_id: int | None = None
    preferred_start_seconds: float | None = None
    discussion_sort: str = "popular"
