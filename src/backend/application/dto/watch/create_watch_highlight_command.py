"""Create a highlight from the player with playback context."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateWatchHighlightCommand:
    """Create a highlight from the player with playback context.

    Attributes:
        user_id: Owner user identifier.
        anime_id: Anime identifier.
        episode: Episode number.
        title: Highlight title.
        category: Optional category.
        start_timestamp: Start time in seconds.
        end_timestamp: End time in seconds.
        description: Optional description.
        is_spoiler: Whether the highlight contains spoilers.
        emotion: Optional emotion label.
        watch_source_id: Active watch source identifier.
        translation_id: Translation identifier.
    """

    user_id: int
    anime_id: int
    episode: int
    title: str
    category: str | None
    start_timestamp: float
    end_timestamp: float
    description: str
    is_spoiler: bool
    emotion: str | None
    watch_source_id: int
    translation_id: int
