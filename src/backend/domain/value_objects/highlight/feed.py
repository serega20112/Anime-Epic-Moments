"""Страница ленты хайлайтов."""

from dataclasses import dataclass, field

from backend.domain.value_objects.highlight.cards import HighlightCard


@dataclass(frozen=True)
class HighlightFeedPage:
    """Страница ленты хайлайтов с метаданными пагинации."""

    items: list[HighlightCard]
    popular_items: list[HighlightCard]
    recent_items: list[HighlightCard]
    liked_items: list[HighlightCard]
    from_favorites_items: list[HighlightCard]
    anime_groups: list["HighlightAnimeGroup"]
    categories: list[str]
    selected_anime_id: int | None
    selected_category: str | None
    include_spoilers: bool
    profile: object | None = None
    recent_activity: list = field(default_factory=list)


@dataclass(frozen=True)
class HighlightAnimeGroup:
    """Группа хайлайтов одного аниме в ленте."""

    anime_id: int
    anime_title: str
    count: int
