"""Data transfer objects for highlight commands and queries."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CreateHighlightCommand:
    """Create highlight payload.

    Attributes:
        user_id: Owner user identifier or None for guests.
        anime_id: Anime identifier.
        episode: Episode number.
        start_timestamp: Start time in seconds.
        end_timestamp: End time in seconds.
        title: Highlight title.
        category: Optional category.
        description: Optional description.
        is_spoiler: Whether the highlight contains spoilers.
        emotion: Optional emotion label.
        highlights_this_hour: Count of highlights created this hour.
    """

    user_id: int | None
    anime_id: int
    episode: int
    start_timestamp: float
    end_timestamp: float
    title: str = ""
    category: str | None = None
    description: str = ""
    is_spoiler: bool = False
    emotion: str | None = None
    highlights_this_hour: int = 0


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


@dataclass(frozen=True, slots=True)
class DeleteHighlightCommand:
    """Delete highlight payload.

    Attributes:
        highlight_id: Highlight identifier.
    """

    highlight_id: int


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


@dataclass(frozen=True, slots=True)
class HighlightDashboardQuery:
    """Pagination and filter parameters shared by dashboard reads.

    Attributes:
        anime_id: Optional anime filter.
        emotion: Optional emotion filter.
        category: Optional category filter.
        sort_by: Sort key.
        created_date: Optional creation date filter.
        query: Optional text search.
        include_spoilers: Whether to include spoiler highlights.
        limit: Maximum number of items.
        viewer_user_id: Optional viewer identifier.
    """

    anime_id: int | None = None
    emotion: str | None = None
    category: str | None = None
    sort_by: str = "recent"
    created_date: str | None = None
    query: str | None = None
    include_spoilers: bool = False
    limit: int = 20
    viewer_user_id: int | None = None


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