"""Add a comment to an anime discussion."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AddAnimeCommentCommand:
    """Add a comment to an anime discussion.

    Attributes:
        anime_id: Anime identifier.
        user_id: Author identifier.
        content: Comment text.
    """

    anime_id: int
    user_id: int
    content: str
