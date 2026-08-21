from dataclasses import dataclass, field

from backend.domain.value_objects.highlight.cards import HighlightCard


@dataclass
class HighlightFeedPage:
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


@dataclass
class HighlightAnimeGroup:
    anime_id: int
    anime_title: str
    count: int
