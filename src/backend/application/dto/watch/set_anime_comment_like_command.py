"""Set or remove a like on an anime discussion comment."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SetAnimeCommentLikeCommand:
    """Set or remove a like on an anime discussion comment.

    Attributes:
        comment_id: Comment identifier.
        user_id: Acting user identifier.
        liked: True to like, False to remove like.
    """

    comment_id: int
    user_id: int
    liked: bool
