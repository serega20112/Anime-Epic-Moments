"""Умный профиль: жанровые предпочтения, уровни и достижения."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GenreAffinity:
    """Склонность пользователя к жанру по его истории."""

    name: str
    count: int


@dataclass(frozen=True)
class ProfileMoodInsight:
    """Вывод о настроении профиля по просмотренному."""

    label: str
    description: str
    emoji: str


@dataclass(frozen=True)
class TopAnimeEntry:
    """Строка топа аниме пользователя."""

    anime_id: int
    title: str
    cover_url: str | None
    rating: float | None
    weight: float


@dataclass(frozen=True)
class ViewingHeatmapCell:
    """Ячейка тепловой карты просмотров в умном профиле."""

    date: str
    interactions: int


@dataclass(frozen=True)
class AchievementBadge:
    """Достижение пользователя в профиле."""

    code: str
    title: str
    description: str
    icon: str
    rarity: str


@dataclass(frozen=True)
class ProfileLevel:
    """Уровень профиля и прогресс до следующего."""

    level: int
    xp: int
    next_level_xp: int | None
    progress: float


@dataclass(frozen=True)
class SmartProfile:
    """Сводный умный профиль пользователя."""

    favorite_genres: list[GenreAffinity]
    dominant_mood: ProfileMoodInsight
    average_rating: float | None
    hours_watched: float
    top_anime: list[TopAnimeEntry]
    heatmap: list[ViewingHeatmapCell]
    achievements: list[AchievementBadge]
    ai_taste_summary: str
