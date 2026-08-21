from dataclasses import dataclass

from backend.domain.value_objects.highlight.cards import HighlightCard, HighlightStats
from backend.domain.value_objects.highlight.feed import HighlightAnimeGroup


@dataclass
class HighlightDashboard:
    items: list[HighlightCard]
    anime_groups: list[HighlightAnimeGroup]
    emotions: list[str]
    categories: list[str]
    stats: HighlightStats
    selected_anime_id: int | None
    selected_emotion: str | None
    selected_category: str | None
    selected_sort: str
    selected_date: str | None
    selected_query: str | None
    include_spoilers: bool
