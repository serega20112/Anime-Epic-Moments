from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.highlight.feed.get_highlight_feed import GetHighlightFeedUseCase


@pytest.mark.unit
class TestGetHighlightFeedUseCase:
    """Юнит-тесты сбора социального фида хайлайтов."""

    def test_execute_signature(self):
        """Что тестируем: конструктор принимает repo, api_client, favorite_repo и опционально user_repo.
        Что передаём: замоканные зависимости.
        Что ожидаем: создание объекта без ошибок.
        """
        use_case = GetHighlightFeedUseCase(AsyncMock(), AsyncMock(), AsyncMock())
        assert use_case.favorite_repo is not None

    async def test_collects_public_and_personal_sections(self):
        """Что тестируем: сбор popular/recent/liked/from_favorites секций.
        Что передаём: viewer_user_id и category с замоканными репозиториями.
        Что ожидаем: все секции заполнены корректно, категории собраны.
        """
        card = SimpleNamespace(anime_id=11, anime_title="Initial D", category="бой")

        class StubFeed(GetHighlightFeedUseCase):
            async def _build_dashboard(self, **kwargs):
                return SimpleNamespace(items=[card for _ in kwargs["highlights"]])

        repo = AsyncMock()
        repo.get_public_top.return_value = ["p"]
        repo.get_public_recent.return_value = ["r"]
        repo.get_liked_by_user.return_value = ["l"]
        repo.get_from_anime_ids.return_value = ["f"]
        repo.get_profile_summary.return_value = SimpleNamespace(
            highlight_count=1, like_count=2, saved_count=3
        )
        repo.get_recent_activity.return_value = [SimpleNamespace(action="like")]
        favorite_repo = AsyncMock()
        favorite_repo.get_by_user.return_value = [SimpleNamespace(anime_id=11)]
        use_case = StubFeed(repo, AsyncMock(), favorite_repo)

        result = await use_case.execute(viewer_user_id=7, category="бой")

        repo.get_public_top.assert_awaited_once_with(12)
        repo.get_public_recent.assert_awaited_once_with(12)
        repo.get_liked_by_user.assert_awaited_once_with(7, limit=12)
        repo.get_from_anime_ids.assert_awaited_once_with([11], limit=12)
        assert result.popular_items == [card]
        assert result.recent_items == [card]
        assert result.liked_items == [card]
        assert result.from_favorites_items == [card]
        assert result.profile.saved_count == 3
        assert result.categories == ["бой"]

    async def test_skips_personal_sections_for_guest(self):
        """Что тестируем: гостю не собираются персональные секции.
        Что передаём: viewer_user_id=None.
        Что ожидаем: liked/from_favorites пусты, favorite_repo не вызывается.
        """
        card = SimpleNamespace(anime_id=11, anime_title="Initial D", category="бой")

        class StubFeed(GetHighlightFeedUseCase):
            async def _build_dashboard(self, **kwargs):
                return SimpleNamespace(items=[card for _ in kwargs["highlights"]])

        repo = AsyncMock()
        repo.get_public_top.return_value = ["p"]
        repo.get_public_recent.return_value = ["r"]
        favorite_repo = AsyncMock()
        use_case = StubFeed(repo, AsyncMock(), favorite_repo)

        result = await use_case.execute(viewer_user_id=None)

        assert result.liked_items == []
        assert result.from_favorites_items == []
        favorite_repo.get_by_user.assert_not_awaited()
