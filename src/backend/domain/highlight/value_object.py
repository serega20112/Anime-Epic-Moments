from dataclasses import dataclass
from typing import List, Optional


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


@dataclass
class HighlightAnimeGroup:
    anime_id: int
    anime_title: str
    count: int


@dataclass
class HighlightStats:
    total_highlights: int
    top_anime_title: str
    average_duration_seconds: float


@dataclass
class HighlightCommentItem:
    id: int
    user_id: int
    username: str
    content: str
    created_at: str


@dataclass
class HighlightLikeUser:
    user_id: int
    username: str
    created_at: str


@dataclass
class HighlightEngagement:
    comments_count: int = 0
    is_liked: bool = False
    is_saved: bool = False


@dataclass
class HighlightActivityItem:
    action: str
    actor_user_id: int
    actor_username: str
    highlight_id: int
    highlight_title: str
    created_at: str


@dataclass
class HighlightProfileSummary:
    highlight_count: int
    like_count: int
    saved_count: int


@dataclass
class HighlightDashboard:
    items: List[HighlightCard]
    anime_groups: List[HighlightAnimeGroup]
    emotions: List[str]
    categories: List[str]
    stats: HighlightStats
    selected_anime_id: Optional[int]
    selected_emotion: str | None
    selected_category: str | None
    selected_sort: str
    selected_date: str | None
    selected_query: str | None
    include_spoilers: bool


@dataclass
class HighlightFeedPage:
    popular_items: List[HighlightCard]
    recent_items: List[HighlightCard]
    liked_items: List[HighlightCard]
    from_favorites_items: List[HighlightCard]
    anime_groups: List[HighlightAnimeGroup]
    categories: List[str]
    selected_anime_id: Optional[int]
    selected_category: str | None
    include_spoilers: bool
    profile: HighlightProfileSummary | None
    recent_activity: List[HighlightActivityItem]
