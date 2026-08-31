from dataclasses import dataclass


@dataclass
class HighlightCard:
    id: int
    anime_id: int
    anime_title: str
    anime_cover: str | None
    title: str
    category: str | None
    episode: int
    start_timestamp: str
    end_timestamp: str
    duration_seconds: float
    description: str
    is_spoiler: bool
    emotion: str | None
    created_at: str
    likes_count: int
    views_count: int
    comments_count: int
    is_liked: bool
    is_saved: bool
    watch_url: str
    share_url: str
    owner_user_id: int | None = None
    owner_username: str | None = None
    owner_avatar_url: str | None = None
    owner_profile_url: str | None = None
    anime_original_title: str | None = None


@dataclass
class HighlightStats:
    total_highlights: int
    top_anime_title: str
    average_duration_seconds: float


@dataclass
class HighlightLikeUser:
    user_id: int
    username: str
    created_at: str


@dataclass
class HighlightCommentItem:
    id: int
    user_id: int
    username: str
    content: str
    created_at: str


@dataclass
class HighlightEngagement:
    comments_count: int = 0
    is_liked: bool = False
    is_saved: bool = False
