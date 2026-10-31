from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import WatchPageQuery
from backend.application.use_cases.watch.page.get_watch_page import GetWatchPageUseCase
from backend.domain import Highlight, Translation, UserAnimeStatus, ViewingSession, WatchSource
from backend.domain.entities.anime.anime import Anime
from backend.domain.value_objects.watch.page_data import TranslationEpisodeCount
from tests.support.fakes import FakeUnitOfWork


def _anime(**overrides) -> Anime:
    """Собрать карточку тайтла из каталога с переопределёнными полями."""
    fields = {
        "title": "Gintama",
        "original_title": "Gintama Kyuu",
        "cover_url": "https://example.com/cover.jpg",
        "description": "Описание тайтла",
        "year": 2011,
        "rating": 8.9,
        "genres": ["Comedy"],
        "episode_count": 12,
        "external_id": "12345",
    }
    fields.update(overrides)
    return Anime(**fields)


def _source(source_id: int, source_name: str) -> WatchSource:
    """Собрать источник просмотра с указанным идентификатором и именем."""
    return WatchSource(
        id=source_id,
        anime_id=7,
        episode=2,
        translation_id=3,
        provider_name="Kinobox",
        source_name=source_name,
        stream_url=f"https://example.com/{source_name}.m3u8",
        quality_label="720p",
        source_type="stream",
    )


def _highlight() -> Highlight:
    """Собрать хайлайт второй серии без собственного заголовка."""
    highlight = Highlight(
        user_id=4,
        anime_id=7,
        episode=2,
        start_timestamp=10.0,
        end_timestamp=25.0,
    )
    highlight.id = 21
    highlight.likes_count = 3
    return highlight


def _use_case(
    *,
    sources=None,
    anime=_anime(),
    session=None,
    status=None,
    user_rating=None,
    availability=None,
) -> tuple:
    """Собрать сценарий страницы просмотра с двойниками зависимостей."""
    watch_repository = AsyncMock()
    watch_repository.get_translations.return_value = [
        Translation(id=3, anime_id=7, name="AniLibria", translation_type="dub")
    ]
    watch_repository.get_session.return_value = session
    watch_repository.get_status.return_value = status
    watch_repository.get_highlight_contexts.return_value = [
        SimpleNamespace(highlight_id=21, watch_source_id=11, translation_id=3, title="Финал заезда")
    ]
    highlight_repository = AsyncMock()
    highlight_repository.get_by_anime_episode.return_value = [_highlight()]
    rating_repository = AsyncMock()
    rating_repository.get_user_rating.return_value = user_rating
    anime_api_client = AsyncMock()
    anime_api_client.get_by_id.return_value = anime
    sync_service = AsyncMock()
    sync_service.sync_for_anime.return_value = sources if sources is not None else []
    sync_service.get_translations_availability.return_value = (
        availability if availability is not None else []
    )
    sync_service.is_enabled.return_value = True
    sync_service.get_provider_label.return_value = "Kinobox"
    uow = FakeUnitOfWork(
        WatchRepository=watch_repository,
        HighlightRepository=highlight_repository,
        RatingRepository=rating_repository,
    )
    use_case = GetWatchPageUseCase(uow, anime_api_client, sync_service)
    return use_case, watch_repository, highlight_repository, rating_repository, sync_service


@pytest.mark.unit
class TestGetWatchPageUseCase:
    """Юнит-тесты сборки страницы просмотра аниме."""

    async def test_builds_page_for_guest_from_local_and_external_data(self):
        """Что тестируем: сборку страницы гостя из базы, каталога и провайдера.
        Что передаём: две дорожки-источника, хайлайт с контекстом и карту серий.
        Что ожидаем: карточки, счётчики озвучек и доступные серии собраны.
        """
        record = SimpleNamespace(title="AniLibria", available_episodes=[1, 2, 3], episodes_count=3)
        use_case, watch_repository, _highlights, rating_repository, _service = _use_case(
            sources=[_source(11, "kb-1"), _source(12, "kb-2")],
            availability=[record],
        )

        page = await use_case.execute(WatchPageQuery(anime_id=7, episode=2))

        assert page.anime_title == "Gintama"
        assert page.anime_rating == 8.9
        assert page.episode_total == 3
        assert page.translation_episode_counts == [
            TranslationEpisodeCount(translation_name="AniLibria", available_count=3, is_active=True)
        ]
        assert [item.source_id for item in page.sources] == [11, 12]
        assert page.selected_source_id == 11
        assert page.selected_translation_id == 3
        assert page.highlights[0].title == "Финал заезда"
        assert page.highlights[0].translation_name == "AniLibria"
        assert page.highlights[0].provider_name == "Kinobox"
        assert page.highlights[0].start_timestamp == "00:10"
        assert page.user_rating is None
        watch_repository.get_session.assert_not_awaited()
        rating_repository.get_user_rating.assert_not_awaited()

    async def test_drops_duplicate_sources_and_prefers_session_source(self):
        """Что тестируем: выбор источника из сессии и снятие точных дублей.
        Что передаём: сессию с source_id=12 и список с повторяющимся источником.
        Что ожидаем: активен источник сессии, дубль отброшен, прогресс подставлен.
        """
        session = ViewingSession(
            id=99,
            user_id=4,
            anime_id=7,
            episode=2,
            watch_source_id=12,
            position_seconds=77.5,
            volume=0.5,
            quality_label="480p",
            is_paused=True,
        )
        use_case, watch_repository, _highlights, rating_repository, _service = _use_case(
            sources=[_source(12, "kb-2"), _source(11, "kb-1"), _source(11, "kb-1")],
            session=session,
            status=UserAnimeStatus(user_id=4, anime_id=7, status="watching"),
            user_rating=9,
        )

        page = await use_case.execute(WatchPageQuery(anime_id=7, episode=2, user_id=4))

        watch_repository.get_session.assert_awaited_once_with(user_id=4, anime_id=7, episode=2)
        rating_repository.get_user_rating.assert_awaited_once_with(user_id=4, anime_id=7)
        assert [item.source_id for item in page.sources] == [12, 11]
        assert page.selected_source_id == 12
        assert page.last_position_seconds == 77.5
        assert page.saved_volume == 0.5
        assert page.saved_quality_label == "480p"
        assert page.current_status == "watching"
        assert page.user_rating == 9

    async def test_falls_back_to_catalog_defaults_without_anime_card(self):
        """Что тестируем: поведение страницы при отсутствии карточки тайтла.
        Что передаём: каталог вернул None, провайдер не нашёл источников.
        Что ожидаем: запасной заголовок и описание, пустые источники, серия как итог.
        """
        use_case, _watch, _highlights, _rating, service = _use_case(sources=[], anime=None)
        service.get_translations_availability.return_value = None

        page = await use_case.execute(WatchPageQuery(anime_id=7, episode=2))

        assert page.anime_title == "Anime #7"
        assert page.anime_description == "Описание недоступно"
        assert page.genres == []
        assert page.sources == []
        assert page.selected_source_id is None
        assert page.episode_total == 2
        assert page.translation_episode_counts == []
