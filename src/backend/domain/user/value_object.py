from dataclasses import dataclass

from src.backend.domain.highlight.value_object import (
    HighlightActivityItem,
    HighlightCard,
    HighlightProfileSummary,
)


@dataclass
class GenreAffinity:
    name: str
    count: int


@dataclass
class ProfileMoodInsight:
    label: str
    description: str
    emoji: str


@dataclass
class TopAnimeEntry:
    anime_id: int
    title: str
    cover_url: str | None
    rating: float | None
    weight: float


@dataclass
class ViewingHeatmapCell:
    date: str
    interactions: int


@dataclass
class AchievementBadge:
    code: str
    title: str
    description: str
    icon: str
    rarity: str


@dataclass
class SmartProfile:
    favorite_genres: list[GenreAffinity]
    dominant_mood: ProfileMoodInsight
    average_rating: float | None
    hours_watched: float
    top_anime: list[TopAnimeEntry]
    heatmap: list[ViewingHeatmapCell]
    achievements: list[AchievementBadge]
    ai_taste_summary: str


@dataclass
class ProfileOverview:
    user_id: int
    email: str
    username: str
    avatar_url: str | None
    created_at: str
    summary: HighlightProfileSummary
    recent_highlights: list[HighlightCard]
    popular_highlights: list[HighlightCard]
    liked_highlights: list[HighlightCard]
    saved_highlights: list[HighlightCard]
    recent_activity: list[HighlightActivityItem]
    smart_profile: SmartProfile


@dataclass
class PendingEmailVerification:
    email: str
    username: str
    password_hash: str
    code: str
    theme: str = "neon"
