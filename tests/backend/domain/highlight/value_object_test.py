from __future__ import annotations

from dataclasses import asdict

from src.backend.domain.highlight.value_object import (
    HighlightAnimeGroup,
    HighlightCard,
    HighlightDashboard,
    HighlightStats,
)


def test_highlight_value_objects_store_dashboard_shape():
    """Проверяем, что value objects дашборда хранят ожидаемую структуру данных."""
    card = HighlightCard(
        id=1,
        anime_id=7,
        anime_title="Gintama",
        anime_cover="https://example.com/gintama.jpg",
        episode=3,
        start_timestamp="00:15",
        end_timestamp="00:45",
        duration_seconds=30.0,
        description="best joke",
        is_spoiler=False,
        emotion="funny",
        created_at="2026-03-28",
        likes_count=5,
        watch_url="/watch/7?episode=3",
        share_url="/highlights?highlight_id=1",
    )
    group = HighlightAnimeGroup(anime_id=7, anime_title="Gintama", count=2)
    stats = HighlightStats(
        total_highlights=1,
        top_anime_title="Gintama",
        average_duration_seconds=30.0,
    )
    dashboard = HighlightDashboard(
        items=[card],
        anime_groups=[group],
        emotions=["funny"],
        stats=stats,
        selected_anime_id=7,
        selected_emotion="funny",
        selected_date="2026-03-28",
        selected_query="joke",
        include_spoilers=False,
    )

    assert asdict(dashboard)["stats"]["top_anime_title"] == "Gintama"
    assert asdict(dashboard)["items"][0]["watch_url"] == "/watch/7?episode=3"
