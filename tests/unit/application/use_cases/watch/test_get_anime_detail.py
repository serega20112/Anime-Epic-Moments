from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import GetFavoriteIdsQuery, WatchPageQuery
from backend.application.use_cases.watch.page.get_anime_detail import GetAnimeDetailUseCase
from backend.domain.entities.watch.user_anime_status import UserAnimeStatus
from backend.domain.value_objects.watch.page_data import WatchPageData
from tests.support.fakes import FakeUnitOfWork


def _page(**overrides) -> WatchPageData:
    """Собрать минимальные данные страницы просмотра с переопределениями."""
    fields = {
        "anime_id": 7,
        "anime_title": "Gintama",
        "anime_cover": None,
        "anime_description": "Описание",
        "anime_year": 2011,
        "anime_rating": 8.9,
        "genres": ["Comedy"],
        "episode": 2,
        "episode_total": 3,
        "episode_options": [1, 2, 3],
        "selected_source_id": None,
        "selected_translation_id": None,
        "sources": [],
        "highlights": [],
        "current_status": None,
        "last_position_seconds": 0.0,
        "preferred_start_seconds": 0.0,
        "saved_volume": 1.0,
        "saved_quality_label": None,
        "user_rating": None,
    }
    fields.update(overrides)
    return WatchPageData(**fields)


def _use_case(*, page, favorite_ids, status):
    """Собрать сценарий карточки с двойниками зависимости."""
    watch_page = AsyncMock()
    watch_page.execute.return_value = page
    favorites = AsyncMock()
    favorites.execute.return_value = favorite_ids
    watch_repository = AsyncMock()
    watch_repository.get_status.return_value = status
    uow = FakeUnitOfWork(WatchRepository=watch_repository)
    return (
        GetAnimeDetailUseCase(uow, watch_page, favorites),
        watch_page,
        favorites,
        watch_repository,
    )


@pytest.mark.unit
class TestGetAnimeDetailUseCase:
    """Юнит-тесты сборки карточки тайтла для мобильного клиента."""

    async def test_owner_gets_favorite_flag_and_episode_progress(self):
        """Что тестируем: карточку владельца с избранным и прогрессом серий.
        Что передаём: страницу, избранное с этим тайтлом и дневник на 2 серии.
        Что ожидаем: favorites истина, серия 1 помечена просмотренной, позиция
        только у текущей серии.
        """
        page = _page(current_status="watching", user_rating=8, last_position_seconds=40.0)
        status = UserAnimeStatus(user_id=4, anime_id=7, status="watching", current_episode=2)
        use_case, watch_page, favorites, _repo = _use_case(
            page=page, favorite_ids=[7], status=status
        )

        detail = await use_case.execute(WatchPageQuery(anime_id=7, episode=2, user_id=4))

        assert detail.favorites is True
        assert detail.page.anime_title == "Gintama"
        assert detail.page.user_rating == 8
        by_number = {item.number: item for item in detail.episodes}
        assert by_number[1].watched is True
        assert by_number[2].watched is False
        assert by_number[2].position_seconds == 40.0
        assert by_number[3].position_seconds == 0.0
        favorites.execute.assert_awaited_once_with(GetFavoriteIdsQuery(user_id=4))
        watch_page.execute.assert_awaited_once()

    async def test_guest_card_has_no_personal_state(self):
        """Что тестируем: карточку гостя без персональных полей.
        Что передаём: запрос без идентификатора зрителя.
        Что ожидаем: favorites ложь, сценарий избранного и статус не вызываются,
        серии не помечены просмотренными.
        """
        page = _page()
        use_case, _watch_page, favorites, repo = _use_case(page=page, favorite_ids=[], status=None)

        detail = await use_case.execute(WatchPageQuery(anime_id=7, episode=1))

        assert detail.favorites is False
        assert all(item.watched is False for item in detail.episodes)
        favorites.execute.assert_not_awaited()
        repo.get_status.assert_not_awaited()
