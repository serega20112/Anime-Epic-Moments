from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import HighlightFeedQuery
from backend.application.use_cases.highlight.feed.get_highlight_feed import GetHighlightFeedUseCase
from backend.domain import Highlight
from tests.support.fakes import FakeUnitOfWork


def _highlight(highlight_id: int, *, category: str = "бой") -> Highlight:
    """Собрать публичный хайлайт с указанным идентификатором и категорией."""
    highlight = Highlight(
        user_id=7,
        anime_id=11,
        episode=1,
        start_timestamp=1.0,
        end_timestamp=6.0,
        title="Эпичный старт",
        category=category,
    )
    highlight.id = highlight_id
    return highlight


def _use_case() -> tuple:
    """Собрать сценарий ленты с двойниками репозиториев хайлайтов и избранного."""
    highlight = _highlight(1)
    highlight_repository = AsyncMock()
    highlight_repository.get_public_top.return_value = [highlight]
    highlight_repository.get_public_recent.return_value = [highlight]
    highlight_repository.get_liked_by_user.return_value = [highlight]
    highlight_repository.get_from_anime_ids.return_value = [highlight]
    highlight_repository.get_engagement_map.return_value = {}
    highlight_repository.get_profile_summary.return_value = SimpleNamespace(
        highlight_count=1, like_count=2, saved_count=3
    )
    highlight_repository.get_recent_activity.return_value = [SimpleNamespace(action="like")]
    favorite_repository = AsyncMock()
    favorite_repository.get_by_user.return_value = [SimpleNamespace(anime_id=11)]
    user_repository = AsyncMock()
    user_repository.get_by_ids.return_value = []
    anime_api_client = AsyncMock()
    anime_api_client.get_by_id.return_value = None
    uow = FakeUnitOfWork(
        HighlightRepository=highlight_repository,
        FavoriteRepository=favorite_repository,
        UserRepository=user_repository,
    )
    use_case = GetHighlightFeedUseCase(uow, anime_api_client)
    return use_case, uow, highlight_repository, favorite_repository


@pytest.mark.unit
class TestGetHighlightFeedUseCase:
    """Юнит-тесты сбора социального фида хайлайтов."""

    async def test_collects_public_and_personal_sections(self):
        """Что тестируем: сбор секций popular/recent/liked/from_favorites.
        Что передаём: зрителя с фильтром по категории.
        Что ожидаем: все секции заполнены, категории и профиль собраны.
        """
        use_case, uow, repository, favorites = _use_case()

        page = await use_case.execute(HighlightFeedQuery(viewer_user_id=7, category="бой"))

        assert uow.commits == 1
        repository.get_public_top.assert_awaited_once_with(12)
        repository.get_public_recent.assert_awaited_once_with(12)
        repository.get_liked_by_user.assert_awaited_once_with(7, limit=12)
        repository.get_from_anime_ids.assert_awaited_once_with([11], limit=12)
        favorites.get_by_user.assert_awaited_once_with(7)
        assert len(page.popular_items) == 1
        assert len(page.recent_items) == 1
        assert len(page.liked_items) == 1
        assert len(page.from_favorites_items) == 1
        assert page.profile.saved_count == 3
        assert page.recent_activity[0].action == "like"
        assert page.categories == ["бой"]
        assert page.anime_groups[0].count == 4

    async def test_skips_personal_sections_for_guest(self):
        """Что тестируем: отсутствие персональных секций у гостя.
        Что передаём: запрос без зрителя.
        Что ожидаем: liked/from_favorites пусты, избранное не читается.
        """
        use_case, _uow, repository, favorites = _use_case()

        page = await use_case.execute(HighlightFeedQuery(viewer_user_id=None))

        repository.get_liked_by_user.assert_not_awaited()
        repository.get_from_anime_ids.assert_not_awaited()
        favorites.get_by_user.assert_not_awaited()
        assert page.liked_items == []
        assert page.from_favorites_items == []
        assert page.profile is None
        assert len(page.items) == 2

    async def test_drops_highlights_outside_category_filter(self):
        """Что тестируем: фильтр публичной ленты по категории.
        Что передаём: категорию «драма» при хайлайте категории «бой».
        Что ожидаем: публичные секции пусты, категории не собраны.
        """
        use_case, _uow, _repository, _favorites = _use_case()

        page = await use_case.execute(HighlightFeedQuery(category="драма"))

        assert page.popular_items == []
        assert page.recent_items == []
        assert page.categories == []
