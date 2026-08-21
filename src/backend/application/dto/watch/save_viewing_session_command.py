"""Persist the user's viewing session position."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SaveViewingSessionCommand:
    """Persist the user's viewing session position.

    Attributes:
        user_id: Acting user identifier.
        anime_id: Anime identifier.
        episode: Episode number.
        watch_source_id: Active watch source identifier.
        position_seconds: Playback position in seconds.
        volume: Player volume (0.0 to 1.0).
        quality_label: Selected quality label.
        is_paused: Whether playback was paused.
    """

    user_id: int
    anime_id: int
    episode: int
    watch_source_id: int
    position_seconds: float = 0.0
    volume: float = 1.0
    quality_label: str = "Auto"
    is_paused: bool = False
