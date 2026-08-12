from __future__ import annotations

from dataclasses import asdict

import pytest

from backend.domain.highlight.value_object import (
    HighlightActivityItem,
    HighlightAnimeGroup,
    HighlightCard,
    HighlightDashboard,
    HighlightFeedPage,
    HighlightProfileSummary,
    HighlightStats,
)


class TestHighlightValueObjects:
    """Юнит-тесты value objects дашборда и фида хайлайтов."""

    def _build_card(self) -> HighlightCard:
        return HighlightCard(
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

    @pytest.mark.unit
    def test_dashboard_stores_stats_and_selections(self):
        """Что тестируем: value objects дашборда хайлайтов.

        Что передаём: карточки, группы по аниме, статистику и параметры выборки.
        Что ожидаем: дашборд сохраняет статистику, карточки и выбранные фильтры.
        """
        card = self._build_card()
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

        payload = asdict(dashboard)

        assert payload["stats"]["top_anime_title"] == "Gintama"
        assert payload["items"][0]["share_url"] == "/highlights/share/1"
        assert payload["selected_sort"] == "popular"

    @pytest.mark.unit
    def test_feed_page_stores_segments_and_groups(self):
        """Что тестируем: value object HighlightFeedPage.

        Что передаём: карточку хайлайта и группу аниме.
        Что ожидаем: страница сохраняет сегменты фида, группы и категории.
        """
        card = self._build_card()
        group = HighlightAnimeGroup(anime_id=7, anime_title="Gintama", count=2)
        feed = HighlightFeedPage(
            items=[card],
            popular_items=[card],
            recent_items=[],
            liked_items=[],
            from_favorites_items=[],
            anime_groups=[group],
            categories=["комедия"],
            selected_anime_id=None,
            selected_category=None,
            include_spoilers=False,
        )

        payload = asdict(feed)

        assert payload["items"][0]["category"] == "комедия"
        assert payload["popular_items"][0]["id"] == 1
        assert payload["anime_groups"][0]["count"] == 2
        assert payload["categories"] == ["комедия"]

    @pytest.mark.unit
    def test_profile_summary_and_activity_item_shape(self):
        """Что тестируем: value objects сводки профиля и активности.

        Что передаём: счётчики профиля и элемент последней активности.
        Что ожидаем: словари содержат корректные значения счётчиков и действия.
        """
        summary = HighlightProfileSummary(highlight_count=1, like_count=2, saved_count=3)
        activity = HighlightActivityItem(
            action="like",
            actor_user_id=2,
            actor_username="viewer",
            highlight_id=1,
            highlight_title="Лучший момент",
            created_at="2026-03-28 12:00",
        )

        assert asdict(summary)["saved_count"] == 3
        assert asdict(activity)["action"] == "like"
        assert asdict(activity)["actor_username"] == "viewer"