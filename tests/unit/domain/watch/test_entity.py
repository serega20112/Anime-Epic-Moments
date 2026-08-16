from __future__ import annotations

import pytest

from backend.domain.watch.entity import (
    HighlightContext,
    Translation,
    UserAnimeStatus,
    ViewingSession,
    WatchSource,
)


class TestWatchEntities:
    """Юнит-тесты watch-сущностей домена."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("factory", "attrs"),
        [
            (
                lambda: UserAnimeStatus(user_id=1, anime_id=7, status="watching"),
                {"user_id": 1, "anime_id": 7, "status": "watching"},
            ),
            (
                lambda: Translation(anime_id=7, name="AniLibria", translation_type="voice"),
                {"anime_id": 7, "name": "AniLibria", "translation_type": "voice"},
            ),
            (
                lambda: WatchSource(
                    anime_id=7,
                    episode=3,
                    translation_id=4,
                    provider_name="Kodik",
                    source_name="source-1",
                    stream_url="https://example.com/stream.m3u8",
                    quality_label="1080",
                ),
                {"episode": 3, "translation_id": 4, "provider_name": "Kodik"},
            ),
            (
                lambda: ViewingSession(
                    user_id=1,
                    anime_id=7,
                    episode=3,
                    watch_source_id=4,
                    position_seconds=55.5,
                    volume=0.7,
                    quality_label="1080",
                    is_paused=True,
                ),
                {"watch_source_id": 4, "position_seconds": 55.5, "is_paused": True},
            ),
            (
                lambda: HighlightContext(
                    highlight_id=2,
                    watch_source_id=4,
                    translation_id=3,
                    title="clip",
                ),
                {"highlight_id": 2, "watch_source_id": 4, "translation_id": 3},
            ),
        ],
    )
    def test_watch_entities_store_provided_fields_and_timestamps(self, factory, attrs):
        """Что тестируем: конструкторы UserAnimeStatus, Translation, WatchSource, ViewingSession, HighlightContext.

        Что передаём: различные наборы полей для каждой watch-сущности.
        Что ожидаем: переданные поля сохраняются, а по умолчанию выставляется timestamp.
        """
        entity = factory()

        for name, value in attrs.items():
            assert getattr(entity, name) == value
        assert any(
            getattr(entity, field, None) is not None for field in ("updated_at", "created_at")
        )
