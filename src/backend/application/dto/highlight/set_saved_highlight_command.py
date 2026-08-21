"""Save or unsave a highlight payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SetSavedHighlightCommand:
    """Save or unsave a highlight payload.

    Attributes:
        highlight_id: Highlight identifier.
        user_id: Acting user identifier.
        saved: True to save, False to remove from saved.
    """

    highlight_id: int
    user_id: int
    saved: bool
