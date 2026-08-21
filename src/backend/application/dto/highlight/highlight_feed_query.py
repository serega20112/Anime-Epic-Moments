"""Filter parameters for the social highlight feed."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HighlightFeedQuery:
    """Filter parameters for the social highlight feed.

    Attributes:
        anime_id: Optional anime filter.
        category: Optional category filter.
        include_spoilers: Whether to include spoiler highlights.
        limit: Maximum number of items.
        viewer_user_id: Optional viewer identifier.
    """

    anime_id: int | None = None
    category: str | None = None
    include_spoilers: bool = False
    limit: int = 12
    viewer_user_id: int | None = None
