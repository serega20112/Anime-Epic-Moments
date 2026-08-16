from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import WatchPageQuery
from backend.application.use_cases import GetWatchPageUseCase
from backend.domain import Highlight, Translation, ViewingSession, WatchSource


@pytest.mark.unit
class TestGetWatchPageUseCase:
    """Юнит-тесты сборки страницы просмотра аниме."""

    async def test_builds_sorted_sources_and_highlight_cards(self, anime_factory):
        """Что тестируем: сортировку источников, использование сессии и сборку highlight cards.
        Что передаём: аниме, источники, озвучки, сессию и хайлайты.
        Что ожидаем: page с отсортированными источниками и карточками хайлайтов.
        """
        anime = anime_factory(
            external_id="185",
            title="Initial D",
            description="Street racing",
            genres=["Action", "Cars"],
            rating=8.7,
        )
        watch_repo = AsyncMock()
        highlight_repo = AsyncMock()
        anime_api_client = AsyncMock()
        anime_api_client.get_by_id.return_value = anime
        sync_service = AsyncMock()
        sync_service.sync_for_anime.return_value = [
            WatchSource(
                id=3,
                anime_id=185,
                episode=2,
                translation_id=2,
                provider_name="YouTube",
                source_name="clip",
                stream_url="https://youtube.example/embed/1",
                quality_label="YouTube",
                source_type="embed",
            ),
            WatchSource(
                id=2,
                anime_id=185,
                episode=2,
                translation_id=1,
                provider_name="Kodik",
                source_name="main-720",
                stream_url="https://example.com/720.m3u8",
                quality_label="720",
                source_type="stream",
            ),
            WatchSource(
                id=1,
                anime_id=185,
                episode=2,
                translation_id=1,
                provider_name="Kodik",
                source_name="main-1080",
                stream_url="https://example.com/1080.m3u8",
                quality_label="1080",
                source_type="stream",
            ),
        ]
        watch_repo.get_translations.return_value = [
            Translation(id=1, anime_id=185, name="StudioBand", translation_type="voice"),
            Translation(id=2, anime_id=185, name="Other Team", translation_type="voice"),
        ]
        watch_repo.get_session.return_value = ViewingSession(
            id=10,
            user_id=1,
            anime_id=185,
            episode=2,
            watch_source_id=1,
            position_seconds=75.0,
            volume=0.6,
            quality_label="1080",
            is_paused=True,
        )
        watch_repo.get_status.return_value = SimpleNamespace(status="watching")
        watch_repo.get_highlight_contexts.return_value = [
            SimpleNamespace(highlight_id=8, watch_source_id=1, translation_id=1, title="best drift")
        ]
        highlight = Highlight(
            user_id=1,
            anime_id=185,
            episode=2,
            start_timestamp=30.0,
            end_timestamp=50.0,
            description="cool scene",
            emotion="hype",
            created_at=datetime(2026, 3, 28),
        )
        highlight.id = 8
        highlight_repo.get_by_anime_episode.return_value = [highlight]
        sync_service.is_enabled.return_value = True
        sync_service.get_provider_label.return_value = "Kodik + YouTube"
        use_case = GetWatchPageUseCase(
            watch_repo,
            highlight_repo,
            anime_api_client,
            sync_service,
            AsyncMock(),
        )

        page = await use_case.execute(
            anime_id=185,
            query=WatchPageQuery(episode=2),
            user_id=1,
        )

        assert [item.source_id for item in page.sources] == [1, 2, 3]
        assert page.selected_source_id == 1
        assert page.selected_translation_id == 1
        assert page.episode_total == 12
        assert page.episode_options[:3] == [1, 2, 3]
        assert page.episode_options[-1] == 12
        assert page.current_status == "watching"
        assert page.last_position_seconds == 75.0
        assert page.preferred_start_seconds == 0.0
        assert page.saved_volume == 0.6
        assert page.highlights[0].title == "best drift"
        assert page.highlights[0].translation_name == "StudioBand"
        assert page.highlights[0].provider_name == "Kodik"
        assert page.discovery_provider_name == "Kodik + YouTube"

    async def test_uses_fallbacks_when_anime_and_sources_are_missing(self):
        """Что тестируем: fallback-данные при отсутствии аниме и источников.
        Что передаём: неизвестное аниме без источников и сессии.
        Что ожидаем: page с дефолтными полями.
        """
        watch_repo = AsyncMock()
        watch_repo.get_translations.return_value = []
        watch_repo.get_highlight_contexts.return_value = []
        highlight_repo = AsyncMock()
        highlight_repo.get_by_anime_episode.return_value = []
        anime_api_client = AsyncMock()
        anime_api_client.get_by_id.return_value = None
        sync_service = AsyncMock()
        sync_service.sync_for_anime.return_value = []
        sync_service.is_enabled.return_value = False
        sync_service.get_provider_label.return_value = None
        use_case = GetWatchPageUseCase(
            watch_repo,
            highlight_repo,
            anime_api_client,
            sync_service,
            AsyncMock(),
        )

        page = await use_case.execute(
            anime_id=999,
            query=WatchPageQuery(episode=1, preferred_start_seconds=42.0),
            user_id=None,
        )

        assert page.anime_title == "Anime #999"
        assert page.anime_description == "Описание недоступно"
        assert page.episode_total == 1
        assert page.episode_options == [1]
        assert page.selected_source_id is None
        assert page.sources == []
        assert page.highlights == []
        assert page.preferred_start_seconds == 42.0
        assert page.can_discover_sources is False
