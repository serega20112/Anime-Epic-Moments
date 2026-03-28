from __future__ import annotations

from src.backend.domain.highlight.value_object import (
    HighlightAnimeGroup,
    HighlightCard,
    HighlightDashboard,
    HighlightStats,
)
from src.backend.infrastructure.cache.highlight_dashboard_cache import (
    HighlightDashboardCache,
)
from src.backend.infrastructure.cache.key_value_store import KeyValueStore


def _dashboard() -> HighlightDashboard:
    return HighlightDashboard(
        items=[
            HighlightCard(
                id=1,
                anime_id=2,
                anime_title="Title",
                anime_cover=None,
                episode=1,
                start_timestamp="00:10",
                end_timestamp="00:20",
                duration_seconds=10.0,
                description="desc",
                is_spoiler=False,
                emotion="hype",
                created_at="2026-03-28",
                likes_count=0,
                watch_url="/watch/2?episode=1",
                share_url="/highlights?highlight_id=1",
            )
        ],
        anime_groups=[HighlightAnimeGroup(anime_id=2, anime_title="Title", count=1)],
        emotions=["hype"],
        stats=HighlightStats(
            total_highlights=1,
            top_anime_title="Title",
            average_duration_seconds=10.0,
        ),
        selected_anime_id=None,
        selected_emotion=None,
        selected_date=None,
        selected_query=None,
        include_spoilers=False,
    )


def test_highlight_dashboard_cache_returns_saved_public_dashboard():
    """Проверяем, что HighlightDashboardCache возвращает сохраненный публичный дашборд."""
    cache = HighlightDashboardCache(store=KeyValueStore(redis_url=None, namespace="test"))
    expected = _dashboard()

    cache.set_public(
        limit=10,
        anime_id=None,
        emotion=None,
        created_date=None,
        query=None,
        include_spoilers=False,
        value=expected,
    )

    assert (
        cache.get_public(
            limit=10,
            anime_id=None,
            emotion=None,
            created_date=None,
            query=None,
            include_spoilers=False,
        )
        == expected
    )


def test_highlight_dashboard_cache_invalidates_public_dashboards():
    """Проверяем, что invalidate_public очищает сохраненные публичные дашборды."""
    cache = HighlightDashboardCache(store=KeyValueStore(redis_url=None, namespace="test"))
    cache.set_public(
        limit=10,
        anime_id=None,
        emotion=None,
        created_date=None,
        query=None,
        include_spoilers=False,
        value=_dashboard(),
    )

    cache.invalidate_public()

    assert (
        cache.get_public(
            limit=10,
            anime_id=None,
            emotion=None,
            created_date=None,
            query=None,
            include_spoilers=False,
        )
        is None
    )
