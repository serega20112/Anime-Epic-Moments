from dataclasses import dataclass


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
