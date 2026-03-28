from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

from src.backend.domain.highlight.entity import Highlight
from src.backend.use_case.highlight.get_user_highlights import GetUserHighlightsUseCase


def test_get_user_highlights_builds_dashboard_with_filters_stats_and_sort(anime_factory):
    """Проверяем, что GetUserHighlightsUseCase фильтрует карточки, считает статистику и поддерживает сортировку по популярности."""
    first = Highlight(
        user_id=1,
        anime_id=10,
        episode=2,
        start_timestamp=10.0,
        end_timestamp=25.0,
        title="First",
        category="драма",
        description="best joke",
        emotion="funny",
        created_at=datetime(2026, 3, 28),
    )
    first.id = 7
    first.likes_count = 1
    first.views_count = 1
    second = Highlight(
        user_id=1,
        anime_id=10,
        episode=3,
        start_timestamp=5.0,
        end_timestamp=10.0,
        title="Second",
        category="драма",
        description="best joke too",
        emotion="funny",
        created_at=datetime(2026, 3, 29),
    )
    second.id = 8
    second.likes_count = 4
    second.views_count = 3
    repo = Mock()
    repo.get_by_user.return_value = [first, second]
    repo.get_engagement_map.return_value = {}
    anime_api_client = Mock()
    anime_api_client.get_by_id.side_effect = lambda anime_id: {
        10: anime_factory(external_id="185", title="Initial D", cover_url="https://example.com/cover.jpg"),
    }[anime_id]
    use_case = GetUserHighlightsUseCase(repo, anime_api_client)

    dashboard = use_case.execute(
        user_id=1,
        emotion="funny",
        category="драма",
        query="joke",
        include_spoilers=False,
        sort_by="popular",
    )

    assert len(dashboard.items) == 2
    assert dashboard.items[0].anime_title == "Initial D"
    assert dashboard.items[0].watch_url == "/watch/185?episode=3"
    assert dashboard.stats.total_highlights == 2
    assert dashboard.stats.top_anime_title == "Initial D"
    assert dashboard.stats.average_duration_seconds == 10.0
    assert dashboard.emotions == ["funny"]
    assert dashboard.categories == ["драма"]
    assert dashboard.selected_sort == "popular"


def test_get_user_highlights_uses_fallback_title_when_anime_missing():
    """Проверяем, что GetUserHighlightsUseCase использует fallback title, если карточка аниме не найдена."""
    highlight = Highlight(
        user_id=1,
        anime_id=99,
        episode=1,
        start_timestamp=1.0,
        end_timestamp=2.0,
        created_at=datetime(2026, 3, 28),
    )
    highlight.id = 5
    repo = Mock()
    repo.get_by_user.return_value = [highlight]
    repo.get_engagement_map.return_value = {}
    anime_api_client = Mock()
    anime_api_client.get_by_id.return_value = None
    use_case = GetUserHighlightsUseCase(repo, anime_api_client)

    dashboard = use_case.execute(user_id=1)

    assert dashboard.items[0].anime_title == "Anime #99"
    assert dashboard.items[0].watch_url == "/watch/99?episode=1"
    assert dashboard.selected_sort == "recent"
