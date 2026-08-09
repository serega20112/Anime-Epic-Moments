from __future__ import annotations

from dataclasses import asdict

from backend.domain import (
    HighlightActivityItem,
    HighlightAnimeGroup,
    HighlightCard,
    HighlightDashboard,
    HighlightFeedPage,
    HighlightProfileSummary,
    HighlightStats,
)


def test_highlight_value_objects_store_dashboard_and_feed_shape():
    """Проверяем, что value objects дашборда и фида хранят ожидаемую структуру данных."""
    card = HighlightCard(
        id=1,
        anime_id=7,
        anime_title="Gintama",
        anime_cover="https://example.com/gintama.jpg",
        title="Лучший момент",
        category="комедия",
        episode=3,
        start_timestamp="00:15",
        end_timestamp="00:45",
        duration_seconds=30.0,
        description="best joke",
        is_spoiler=False,
        emotion="funny",
        created_at="2026-03-28",
        likes_count=5,
        views_count=12,
        comments_count=2,
        is_liked=True,
        is_saved=False,
        watch_url="/watch/7?episode=3",
        share_url="/highlights/share/1",
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
        categories=["комедия"],
        stats=stats,
        selected_anime_id=7,
        selected_emotion="funny",
        selected_category="комедия",
        selected_sort="popular",
        selected_date="2026-03-28",
        selected_query="joke",
        include_spoilers=False,
    )
    feed = HighlightFeedPage(
        popular_items=[card],
        recent_items=[card],
        liked_items=[card],
        from_favorites_items=[card],
        anime_groups=[group],
        categories=["комедия"],
        selected_anime_id=7,
        selected_category="комедия",
        include_spoilers=False,
        profile=HighlightProfileSummary(highlight_count=1, like_count=2, saved_count=3),
        recent_activity=[
            HighlightActivityItem(
                action="like",
                actor_user_id=2,
                actor_username="viewer",
                highlight_id=1,
                highlight_title="Лучший момент",
                created_at="2026-03-28 12:00",
            )
        ],
    )

    payload = asdict(feed)

    assert asdict(dashboard)["stats"]["top_anime_title"] == "Gintama"
    assert asdict(dashboard)["items"][0]["share_url"] == "/highlights/share/1"
    assert payload["profile"]["saved_count"] == 3
    assert payload["recent_activity"][0]["action"] == "like"
