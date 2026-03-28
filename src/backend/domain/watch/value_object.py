from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DiscoveredWatchSource:
    episode: int
    translation_name: str
    translation_type: str
    provider_name: str
    source_name: str
    quality_label: str
    stream_url: str
    source_type: str = "stream"
    language: str = "ru"


@dataclass
class WatchSourceCard:
    source_id: int
    translation_id: int
    translation_name: str
    episode: int
    provider_name: str
    source_name: str
    quality_label: str
    stream_url: str
    source_type: str


@dataclass
class WatchHighlightCard:
    id: int
    title: str
    category: str | None
    likes_count: int
    description: str
    start_timestamp: str
    end_timestamp: str
    emotion: str | None
    is_spoiler: bool
    translation_name: str | None
    provider_name: str | None


@dataclass
class WatchPageData:
    anime_id: int
    anime_title: str
    anime_cover: str | None
    anime_description: str
    anime_year: int | None
    anime_rating: float | None
    genres: List[str]
    episode: int
    episode_total: int | None
    episode_options: List[int]
    selected_source_id: Optional[int]
    selected_translation_id: Optional[int]
    sources: List[WatchSourceCard]
    highlights: List[WatchHighlightCard]
    current_status: str | None
    last_position_seconds: float
    saved_volume: float
    saved_quality_label: str | None
    can_discover_sources: bool = False
    discovery_provider_name: str | None = None
