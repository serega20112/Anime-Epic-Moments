from dataclasses import dataclass
from typing import List, Optional


@dataclass
class HighlightCard:
    id: int
    anime_id: int
    anime_title: str
    anime_cover: str | None
    episode: int
    start_timestamp: str
    end_timestamp: str
    duration_seconds: float
    description: str
    is_spoiler: bool
    emotion: str | None
    created_at: str
    likes_count: int
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
class HighlightDashboard:
    items: List[HighlightCard]
    anime_groups: List[HighlightAnimeGroup]
    emotions: List[str]
    stats: HighlightStats
    selected_anime_id: Optional[int]
    selected_emotion: str | None
    selected_date: str | None
    selected_query: str | None
    include_spoilers: bool
