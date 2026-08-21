"""Filter parameters for a user's saved or liked highlight dashboard."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HighlightListQuery:
    """Filter parameters for a user's saved or liked highlight dashboard.

    Attributes:
        anime_id: Optional anime filter.
        emotion: Optional emotion filter.
        category: Optional category filter.
        sort_by: Sort key.
        created_date: Optional creation date filter.
        query: Optional text search.
        include_spoilers: Whether to include spoiler highlights.
    """

    anime_id: int | None = None
    emotion: str | None = None
    category: str | None = None
    sort_by: str = "recent"
    created_date: str | None = None
    query: str | None = None
    include_spoilers: bool = True
