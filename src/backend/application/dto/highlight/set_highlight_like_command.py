"""Set or remove a highlight like payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SetHighlightLikeCommand:
    """Set or remove a highlight like payload.

    Attributes:
        highlight_id: Highlight identifier.
        user_id: Acting user identifier.
        liked: True to like, False to remove like.
    """

    highlight_id: int
    user_id: int
    liked: bool
