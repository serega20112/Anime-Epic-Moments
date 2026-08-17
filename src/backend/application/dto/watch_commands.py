"""Data transfer objects for watch commands and queries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UpsertUserAnimeStatusCommand:
    """Upsert the user's watch status for an anime.

    Attributes:
        user_id: Acting user identifier.
        anime_id: Anime identifier.
        status: Watch status label.
        current_episode: Episode reached by the user.
        rating: Optional personal rating.
        note: Optional personal note.
        started_at: Optional ISO start date.
        completed_at: Optional ISO completion date.
    """

    user_id: int
    anime_id: int
    status: str
    current_episode: int | None = None
    rating: float | None = None
    note: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


@dataclass(frozen=True, slots=True)
class SaveViewingSessionCommand:
    """Persist the user's viewing session position.

    Attributes:
        user_id: Acting user identifier.
        anime_id: Anime identifier.
        episode: Episode number.
        watch_source_id: Active watch source identifier.
        position_seconds: Playback position in seconds.
        volume: Player volume (0.0 to 1.0).
        quality_label: Selected quality label.
        is_paused: Whether playback was paused.
    """

    user_id: int
    anime_id: int
    episode: int
    watch_source_id: int
    position_seconds: float = 0.0
    volume: float = 1.0
    quality_label: str = "Auto"
    is_paused: bool = False


@dataclass(frozen=True, slots=True)
class CreateWatchHighlightCommand:
    """Create a highlight from the player with playback context.

    Attributes:
        user_id: Owner user identifier.
        anime_id: Anime identifier.
        episode: Episode number.
        title: Highlight title.
        category: Optional category.
        start_timestamp: Start time in seconds.
        end_timestamp: End time in seconds.
        description: Optional description.
        is_spoiler: Whether the highlight contains spoilers.
        emotion: Optional emotion label.
        watch_source_id: Active watch source identifier.
        translation_id: Translation identifier.
    """

    user_id: int
    anime_id: int
    episode: int
    title: str
    category: str | None
    start_timestamp: float
    end_timestamp: float
    description: str
    is_spoiler: bool
    emotion: str | None
    watch_source_id: int
    translation_id: int


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


@dataclass(frozen=True, slots=True)
class WatchPageQuery:
    """Query parameters for building the anime watch page.

    Attributes:
        episode: Requested episode number.
        selected_source_id: Optional pre-selected watch source.
        preferred_start_seconds: Optional playback start offset in seconds.
        discussion_sort: Comment sort key ("popular" or "recent").
    """

    episode: int = 1
    selected_source_id: int | None = None
    preferred_start_seconds: float | None = None
    discussion_sort: str = "popular"
