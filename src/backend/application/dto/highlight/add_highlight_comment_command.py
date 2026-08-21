"""Add a highlight comment payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AddHighlightCommentCommand:
    """Add a highlight comment payload.

    Attributes:
        highlight_id: Highlight identifier.
        user_id: Author identifier.
        content: Comment text.
    """

    highlight_id: int
    user_id: int
    content: str
