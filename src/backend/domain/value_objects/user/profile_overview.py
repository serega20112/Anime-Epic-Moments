from dataclasses import dataclass
from datetime import datetime

from backend.domain.value_objects.collection.cards import CollectionCard
from backend.domain.value_objects.highlight.cards import HighlightCard
from backend.domain.value_objects.highlight.profile_summary import (
    HighlightActivityItem,
    HighlightProfileSummary,
)
from backend.domain.value_objects.user.smart_profile import ProfileLevel, SmartProfile


@dataclass
class ViewingHeatmapCell:
    date: str
    interactions: int


@dataclass
class RecentEpisodeCard:
    anime_id: int
    title: str
    original_title: str | None
    cover_url: str | None
    episode: int
    updated_at: datetime


@dataclass
class UserRatingCard:
    anime_id: int
    title: str
    cover_url: str | None
    score: int
    rated_at: str


@dataclass
class ProfileOverview:
    user_id: int
    email: str
    username: str
    avatar_url: str | None
    status: str | None
    show_watch_activity: bool
    show_recent_episodes: bool
    created_at: str
    summary: HighlightProfileSummary
    recent_highlights: list[HighlightCard]
    popular_highlights: list[HighlightCard]
    liked_highlights: list[HighlightCard]
    saved_highlights: list[HighlightCard]
    recent_activity: list[HighlightActivityItem]
    recent_episodes: list[RecentEpisodeCard]
    profile_level: ProfileLevel
    ratings: list[UserRatingCard]
    smart_profile: SmartProfile
    followers_count: int = 0
    following_count: int = 0


@dataclass
class FollowUserCard:
    user_id: int
    username: str
    avatar_url: str | None
    profile_url: str


@dataclass
class PublicProfileOverview:
    profile: ProfileOverview
    public_collections: list[CollectionCard]
    followers_preview: list[FollowUserCard]
    following_preview: list[FollowUserCard]
    followers_count: int
    following_count: int
    is_following: bool
    can_follow: bool
