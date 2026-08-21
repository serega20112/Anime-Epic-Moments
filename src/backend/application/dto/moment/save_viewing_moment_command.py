"""Create or update a draft viewing moment."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SaveViewingMomentCommand:
    """Create or update a draft viewing moment.

    Attributes:
        user_id: Owner user identifier.
        anime_id: Anime identifier.
        episode: Episode number.
        timestamp: Playback position in seconds.
        watch_source_id: Optional active watch source.
        caption: Optional caption for the moment.
        sticker: Optional sticker label.
        screenshot_url: Optional screenshot URL.
        moment_id: Existing moment identifier when updating.
    """

    user_id: int
    anime_id: int
    episode: int
    timestamp: float = 0.0
    watch_source_id: int | None = None
    caption: str | None = None
    sticker: str | None = None
    screenshot_url: str | None = None
    moment_id: int | None = None
