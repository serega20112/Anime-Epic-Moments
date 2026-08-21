"""Create highlight payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateHighlightCommand:
    """Create highlight payload.

    Attributes:
        user_id: Owner user identifier or None for guests.
        anime_id: Anime identifier.
        episode: Episode number.
        start_timestamp: Start time in seconds.
        end_timestamp: End time in seconds.
        title: Highlight title.
        category: Optional category.
        description: Optional description.
        is_spoiler: Whether the highlight contains spoilers.
        emotion: Optional emotion label.
        highlights_this_hour: Count of highlights created this hour.
    """

    user_id: int | None
    anime_id: int
    episode: int
    start_timestamp: float
    end_timestamp: float
    title: str = ""
    category: str | None = None
    description: str = ""
    is_spoiler: bool = False
    emotion: str | None = None
    highlights_this_hour: int = 0
