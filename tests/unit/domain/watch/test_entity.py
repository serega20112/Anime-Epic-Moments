from __future__ import annotations

import pytest

from backend.domain.entities.reaction.episode_reaction import EpisodeReaction
from backend.domain.entities.watch.highlight_context import HighlightContext
from backend.domain.entities.watch.translation import Translation
from backend.domain.entities.watch.user_anime_status import UserAnimeStatus
from backend.domain.entities.watch.viewing_session import ViewingSession
from backend.domain.entities.watch.watch_source import WatchSource
from backend.domain.value_objects.reaction.reaction_type import EpisodeReactionType


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


class TestWatchEntityInvariants:
    """Юнит-тесты инвариантов сущностей просмотра."""

    @pytest.mark.unit
    def test_viewing_session_clamps_player_values(self):
        """Что тестируем: правила позиции, громкости и номера серии.
        Что передаём: отрицательную позицию, громкость за пределами диапазона, нулевую серию.
        Что ожидаем: позиция нулевая, громкость в границах от нуля до единицы,
        серия не меньше первой — плеер не может испортить сохранённый прогресс.
        """
        session = ViewingSession(
            user_id=1,
            anime_id=7,
            episode=0,
            watch_source_id=4,
            position_seconds=-12.0,
            volume=1.8,
            quality_label="1080",
            is_paused=False,
        )
        silent = ViewingSession(
            user_id=1,
            anime_id=7,
            episode=2,
            watch_source_id=4,
            position_seconds=10.0,
            volume=-0.5,
            quality_label="1080",
            is_paused=False,
        )

        assert session.episode == 1
        assert session.position_seconds == 0.0
        assert session.volume == 1.0
        assert silent.volume == 0.0

    @pytest.mark.unit
    def test_watch_source_normalizes_provider_names(self):
        """Что тестируем: канонический вид имён провайдера и источника.
        Что передаём: имена с обрамляющими пробелами и пустой тип источника.
        Что ожидаем: пробелы сняты, тип источника по умолчанию — поток; иначе
        дедупликация и удаление протухших ссылок промахивались бы по имени.
        """
        source = WatchSource(
            anime_id=7,
            episode=3,
            translation_id=4,
            provider_name="  Kodik  ",
            source_name="  kb-1 ",
            stream_url="https://example.com/stream.m3u8",
            quality_label="1080",
            source_type="",
        )

        assert source.provider_name == "Kodik"
        assert source.source_name == "kb-1"
        assert source.source_type == "stream"

    @pytest.mark.unit
    def test_reaction_timestamp_is_not_negative(self):
        """Что тестируем: метку таймлайна реакции.
        Что передаём: отрицательную позицию момента.
        Что ожидаем: она сбрасывается в ноль — реакция не уезжает «до начала серии».
        """
        reaction = EpisodeReaction(
            user_id=1,
            anime_id=7,
            episode=2,
            reaction_type=EpisodeReactionType.FIRE,
            timestamp=-5.0,
        )

        assert reaction.timestamp == 0.0
