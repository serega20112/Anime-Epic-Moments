"""Edit highlight payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EditHighlightCommand:
    """Edit highlight payload.

    Attributes:
        highlight_id: Highlight identifier.
        episode: Episode number.
        start_timestamp: Start time in seconds.
        end_timestamp: End time in seconds.
        title: Highlight title.
        category: Optional category.
        description: Optional description.
        is_spoiler: Whether the highlight contains spoilers.
        emotion: Optional emotion label.
    """

    highlight_id: int
    episode: int | None
    start_timestamp: float
    end_timestamp: float
    title: str
    category: str | None
    description: str
    is_spoiler: bool
    emotion: str | None = None
