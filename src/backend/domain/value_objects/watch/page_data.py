"""Данные страницы просмотра: источники, дневник и статистика."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DiaryEntry:
    """Запись аниме в дневнике пользователя."""

    status: str
    current_episode: int | None
    rating: float | None
    note: str | None
    started_at: str | None
    completed_at: str | None
    last_watched_at: str | None
    anime_id: int
    title: str = ""
    cover_url: str | None = None
    episode_count: int | None = None


@dataclass(frozen=True)
class WatchSourceCard:
    """Карточка источника просмотра с плеером."""

    source_id: int
    translation_id: int
    translation_name: str
    episode: int
    provider_name: str
    source_name: str
    quality_label: str
    stream_url: str
    source_type: str


@dataclass(frozen=True)
class WatchHighlightCard:
    """Карточка хайлайта на странице просмотра."""

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


@dataclass(frozen=True)
class WatchedAnimeStat:
    """Статистика просмотренного аниме."""

    anime_id: int
    watched_seconds: float
    sessions_count: int
    last_watched_at: str


@dataclass(frozen=True)
class TranslationEpisodeCount:
    """Число вышедших серий у конкретной озвучки одного тайтла.

    Attributes:
        translation_name: Название озвучки (студии).
        available_count: Сколько серий реально доступно у этой озвучки.
        is_active: True, если эта озвучка сейчас выбрана в плеере.
    """

    translation_name: str
    available_count: int
    is_active: bool = False


@dataclass(frozen=True)
class ViewingHeatmapPoint:
    """Точка тепловой карты просмотров."""

    date: str
    interactions: int


@dataclass(frozen=True)
class WatchPageData:
    """Полный набор данных для отрисовки страницы просмотра."""

    anime_id: int
    anime_title: str
    anime_cover: str | None
    anime_description: str
    anime_year: int | None
    anime_rating: float | None
    genres: list[str]
    episode: int
    episode_total: int | None
    episode_options: list[int]
    selected_source_id: int | None
    selected_translation_id: int | None
    sources: list[WatchSourceCard]
    highlights: list[WatchHighlightCard]
    current_status: str | None
    last_position_seconds: float
    preferred_start_seconds: float
    saved_volume: float
    saved_quality_label: str | None
    can_discover_sources: bool = False
    discovery_provider_name: str | None = None
    translation_episode_counts: list[TranslationEpisodeCount] = field(default_factory=list)
    anime_title_original: str | None = None
    user_rating: int | None = None
