from __future__ import annotations

from dataclasses import asdict

import pytest

from backend.domain.value_objects.watch.discovery import DiscoveredWatchSource
from backend.domain.value_objects.watch.page_data import (
    ViewingHeatmapPoint,
    WatchedAnimeStat,
    WatchHighlightCard,
    WatchPageData,
    WatchSourceCard,
)


class TestWatchValueObjects:
    """Юнит-тесты value objects страницы просмотра."""

    @pytest.mark.unit
    def test_watch_value_objects_store_page_payload(self):
        """Что тестируем: value objects WatchSourceCard, WatchHighlightCard, WatchPageData.

        Что передаём: сущности с данными источника, хайлайта и полной страницы просмотра.
        Что ожидаем: сериализованная страница содержит все переданные поля и опции эпизодов.
        """
        source = WatchSourceCard(
            source_id=1,
            translation_id=2,
            translation_name="AniLibria",
            episode=3,
            provider_name="Kodik",
            source_name="source-1",
            quality_label="1080",
            stream_url="https://example.com/stream.m3u8",
            source_type="stream",
        )
        highlight = WatchHighlightCard(
            id=9,
            title="best scene",
            category="бой",
            likes_count=8,
            description="moment",
            start_timestamp="00:10",
            end_timestamp="00:20",
            emotion="hype",
            is_spoiler=False,
            translation_name="AniLibria",
            provider_name="Kodik",
        )
        page = WatchPageData(
            anime_id=7,
            anime_title="Gintama",
            anime_cover="https://example.com/cover.jpg",
            anime_description="Comedy",
            anime_year=2006,
            anime_rating=8.9,
            genres=["Comedy"],
            episode=3,
            episode_total=24,
            episode_options=[1, 2, 3],
            selected_source_id=1,
            selected_translation_id=2,
            sources=[source],
            highlights=[highlight],
            current_status="watching",
            last_position_seconds=33.0,
            preferred_start_seconds=10.0,
            saved_volume=0.5,
            saved_quality_label="1080",
            can_discover_sources=True,
            discovery_provider_name="Kodik",
        )

        payload = asdict(page)

        assert payload["anime_title"] == "Gintama"
        assert payload["episode_total"] == 24
        assert payload["episode_options"] == [1, 2, 3]
        assert payload["preferred_start_seconds"] == 10.0
        assert payload["highlights"][0]["category"] == "бой"
        assert payload["sources"][0]["translation_name"] == "AniLibria"

    @pytest.mark.unit
    def test_discovered_and_stat_value_objects_store_fields(self):
        """Что тестируем: value objects DiscoveredWatchSource, WatchedAnimeStat, ViewingHeatmapPoint.

        Что передаём: данные обнаруженного источника, статистику просмотра и точку тепловой карты.
        Что ожидаем: каждый объект сохраняет переданные атрибуты для сериализации.
        """
        discovered = DiscoveredWatchSource(
            episode=3,
            translation_name="AniLibria",
            translation_type="voice",
            provider_name="Kodik",
            source_name="source-1",
            quality_label="1080",
            stream_url="https://example.com/stream.m3u8",
        )
        watched_stat = WatchedAnimeStat(
            anime_id=7,
            watched_seconds=3200.0,
            sessions_count=2,
            last_watched_at="2026-03-28",
        )
        heatmap_point = ViewingHeatmapPoint(date="2026-03-28", interactions=4)

        assert discovered.provider_name == "Kodik"
        assert watched_stat.sessions_count == 2
        assert heatmap_point.interactions == 4
