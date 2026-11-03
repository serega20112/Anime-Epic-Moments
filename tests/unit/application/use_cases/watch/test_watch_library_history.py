from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from backend.application.dto.watch import GetUserHistoryQuery, GetUserLibraryQuery
from backend.application.use_cases.watch.library.get_user_anime_library import (
    GetUserAnimeLibraryUseCase,
)
from backend.application.use_cases.watch.library.get_user_viewing_history import (
    GetUserViewingHistoryUseCase,
)
from backend.domain.entities.anime.anime import Anime
from backend.domain.entities.watch.user_anime_status import UserAnimeStatus
from backend.domain.entities.watch.viewing_session import ViewingSession
from tests.support.fakes import FakeUnitOfWork


def _anime(anime_id: int, title: str) -> Anime:
    """Собрать карточку тайтла каталога с указанным идентификатором и названием."""
    return Anime(external_id=str(anime_id), title=title, genres=["Action"], episode_count=12)


def _status(anime_id: int, status: str, watched_at: datetime, **overrides) -> UserAnimeStatus:
    """Собрать запись дневника с переопределяемыми полями."""
    fields = {
        "user_id": 7,
        "anime_id": anime_id,
        "status": status,
        "last_watched_at": watched_at,
    }
    fields.update(overrides)
    return UserAnimeStatus(**fields)


def _session(anime_id: int, episode: int, position: float, updated_at: datetime) -> ViewingSession:
    """Собрать сессию просмотра с указанным тайтлом, серией и позицией."""
    return ViewingSession(
        user_id=7,
        anime_id=anime_id,
        episode=episode,
        watch_source_id=1,
        position_seconds=position,
        volume=1.0,
        quality_label="Auto",
        is_paused=False,
        updated_at=updated_at,
    )


def _library_use_case(statuses, anime_map):
    """Собрать сценарий библиотеки с двойниками репозитория и каталога."""
    watch_repository = AsyncMock()
    watch_repository.get_statuses_by_user.return_value = statuses
    client = AsyncMock()
    client.get_by_id.side_effect = lambda anime_id: anime_map.get(anime_id)
    uow = FakeUnitOfWork(WatchRepository=watch_repository)
    return GetUserAnimeLibraryUseCase(uow, client), watch_repository, client


def _history_use_case(sessions, anime_map):
    """Собрать сценарий истории с двойниками репозитория и каталога."""
    watch_repository = AsyncMock()
    watch_repository.get_recent_viewing_sessions.return_value = sessions
    client = AsyncMock()
    client.get_by_id.side_effect = lambda anime_id: anime_map.get(anime_id)
    uow = FakeUnitOfWork(WatchRepository=watch_repository)
    return GetUserViewingHistoryUseCase(uow, client), watch_repository, client


@pytest.mark.unit
class TestGetUserAnimeLibraryUseCase:
    """Юнит-тесты чтения библиотеки просмотра."""

    async def test_filters_by_status_and_enriches_from_catalog(self):
        """Что тестируем: фильтр дневника по статусу с обогащением каталога.
        Что передаём: две записи разных статусов и карточки каталога.
        Что ожидаем: только запись нужного статуса, название из каталога.
        """
        early = datetime(2024, 1, 2, tzinfo=UTC)
        late = datetime(2024, 1, 5, tzinfo=UTC)
        use_case, _repo, client = _library_use_case(
            [
                _status(1, "watching", early, current_episode=3, rating=8.0),
                _status(2, "completed", late),
            ],
            {1: _anime(1, "Alpha"), 2: _anime(2, "Beta")},
        )

        cards = await use_case.execute(GetUserLibraryQuery(user_id=7, status="watching"))

        assert [card.anime.title for card in cards] == ["Alpha"]
        assert cards[0].status == "watching"
        assert cards[0].current_episode == 3
        assert cards[0].rating == 8.0
        assert cards[0].last_watched_at == "2024-01-02"
        client.get_by_id.assert_awaited_once_with(1)

    async def test_orders_by_last_watched_desc_and_falls_back_without_catalog(self):
        """Что тестируем: порядок по последнему просмотру и запасную карточку.
        Что передаём: две записи, каталог не отдал карточку для одного тайтла.
        Что ожидаем: более свежий просмотр первым, для отсутствующего — заглушка.
        """
        early = datetime(2024, 1, 2, tzinfo=UTC)
        late = datetime(2024, 1, 5, tzinfo=UTC)
        use_case, _repo, _client = _library_use_case(
            [_status(1, "watching", early), _status(2, "watching", late)],
            {2: _anime(2, "Beta")},
        )

        cards = await use_case.execute(GetUserLibraryQuery(user_id=7))

        assert [card.anime.external_id for card in cards] == ["2", 1]
        assert cards[1].anime.title == "Anime #1"


@pytest.mark.unit
class TestGetUserViewingHistoryUseCase:
    """Юнит-тесты чтения истории просмотров."""

    async def test_projects_sessions_with_catalog_card(self):
        """Что тестируем: проекцию сессий в карточки истории.
        Что передаём: одну сессию и карточку каталога для её тайтла.
        Что ожидаем: серия, позиция, дата и название из каталога собраны.
        """
        stamp = datetime(2024, 3, 10, tzinfo=UTC)
        use_case, repo, _client = _history_use_case(
            [_session(5, 4, 120.5, stamp)],
            {5: _anime(5, "Gamma")},
        )

        cards = await use_case.execute(GetUserHistoryQuery(user_id=7, limit=10))

        repo.get_recent_viewing_sessions.assert_awaited_once_with(7, limit=10)
        assert cards[0].anime.title == "Gamma"
        assert cards[0].episode == 4
        assert cards[0].position_seconds == 120.5
        assert cards[0].watched_at == "2024-03-10"

    async def test_falls_back_to_placeholder_when_catalog_missing(self):
        """Что тестируем: историю при отсутствии карточки в каталоге.
        Что передаём: сессию тайтла, который каталог не вернул.
        Что ожидаем: запасная карточка с идентификатором в названии сохранена.
        """
        stamp = datetime(2024, 3, 10, tzinfo=UTC)
        use_case, _repo, _client = _history_use_case([_session(9, 1, 0.0, stamp)], {})

        cards = await use_case.execute(GetUserHistoryQuery(user_id=7))

        assert cards[0].anime.title == "Anime #9"
