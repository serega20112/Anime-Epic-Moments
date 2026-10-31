from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import PublicProfileQuery
from backend.application.use_cases.user.get_public_profile_overview import (
    GetPublicProfileOverviewUseCase,
)
from backend.domain import HighlightProfileSummary, SmartProfile
from backend.domain.exceptions import NotFoundError
from backend.domain.value_objects.user.smart_profile import ProfileMoodInsight
from tests.support.fakes import FakeUnitOfWork


@pytest.mark.unit
class TestGetPublicProfileOverviewUseCase:
    """Юнит-тесты сценария сборки публичного профиля пользователя."""

    def _profile_payload(self):
        return SimpleNamespace(
            user_id=7,
            email="hidden@example.com",
            username="public-user",
            avatar_url="https://example.com/avatar.png",
            created_at="2026-03-21",
            summary=HighlightProfileSummary(highlight_count=4, like_count=2, saved_count=1),
            recent_highlights=[],
            popular_highlights=[],
            liked_highlights=[],
            saved_highlights=[],
            recent_activity=[],
            smart_profile=SmartProfile(
                favorite_genres=[],
                dominant_mood=ProfileMoodInsight(
                    label="Экшен",
                    description="Любит быстрый темп и напряжение.",
                    emoji="🔥",
                ),
                average_rating=8.8,
                hours_watched=11.5,
                top_anime=[],
                heatmap=[],
                achievements=[],
                ai_taste_summary="Любит быстрый темп.",
            ),
            followers_count=3,
            following_count=2,
        )

    def _user_repository(self, is_following: bool) -> AsyncMock:
        """Собрать двойник репозитория пользователей с social-статистикой."""
        user_repo = AsyncMock()
        user_repo.get_follow_stats.return_value = (3, 2)
        user_repo.get_followers.return_value = [
            SimpleNamespace(id=11, username="follower-1", avatar_url=None)
        ]
        user_repo.get_followed_users.return_value = [
            SimpleNamespace(
                id=12, username="followed-1", avatar_url="https://example.com/followed.png"
            )
        ]
        user_repo.is_following.return_value = is_following
        return user_repo

    def _collection_repository(self) -> AsyncMock:
        """Собрать двойник репозитория коллекций с одной публичной подборкой."""
        collection_repo = AsyncMock()
        collection_repo.get_public_user_collections.return_value = [
            SimpleNamespace(
                id=21,
                title="Ночная подборка",
                description="Только темный вайб",
                is_public=True,
                created_at=datetime(2026, 3, 28),
            )
        ]
        collection_repo.get_items_count_map.return_value = {21: 5}
        return collection_repo

    @pytest.mark.parametrize(
        ("viewer_user_id", "is_following", "can_follow"),
        [
            (None, False, False),
            (5, True, True),
        ],
    )
    async def test_builds_public_payload(self, viewer_user_id, is_following, can_follow):
        """Что тестируем: сборку публичного профиля с social-статистикой.
        Что передаём: query со viewer_user_id и ответ is_following.
        Что ожидаем: профиль и его поля собраны корректно.
        """
        profile_use_case = AsyncMock()
        profile_use_case.execute.return_value = self._profile_payload()
        user_repo = self._user_repository(is_following)
        collection_repo = self._collection_repository()
        use_case = GetPublicProfileOverviewUseCase(
            FakeUnitOfWork(UserRepository=user_repo, CollectionRepository=collection_repo),
            profile_use_case,
        )

        result = await use_case.execute(
            PublicProfileQuery(profile_user_id=7, viewer_user_id=viewer_user_id)
        )

        assert result.ok is True
        data = result.data
        assert data.profile.username == "public-user"
        assert data.followers_count == 3
        assert data.following_count == 2
        assert data.is_following is is_following
        assert data.can_follow is can_follow
        assert data.public_collections[0].title == "Ночная подборка"
        assert data.public_collections[0].items_count == 5
        assert data.followers_preview[0].profile_url == "/users/11"
        assert data.following_preview[0].profile_url == "/users/12"
        collection_repo.get_items_count_map.assert_awaited_once_with([21])
        if viewer_user_id is None:
            user_repo.is_following.assert_not_awaited()
        else:
            user_repo.is_following.assert_awaited_once_with(viewer_user_id, 7)

    async def test_skips_follow_check_for_owner_and_guest(self):
        """Что тестируем: отсутствие проверок подписки для гостя и владельца.
        Что передаём: viewer_user_id=None.
        Что ожидаем: is_following не вызывается, can_follow равен False.
        """
        profile_use_case = AsyncMock()
        profile_use_case.execute.return_value = self._profile_payload()
        user_repo = self._user_repository(is_following=True)
        use_case = GetPublicProfileOverviewUseCase(
            FakeUnitOfWork(
                UserRepository=user_repo, CollectionRepository=self._collection_repository()
            ),
            profile_use_case,
        )

        result = await use_case.execute(PublicProfileQuery(profile_user_id=7))

        assert result.ok is True
        assert result.data.is_following is False
        assert result.data.can_follow is False
        user_repo.is_following.assert_not_awaited()

    async def test_returns_failure_when_profile_use_case_raises_not_found(self):
        """Что тестируем: обработку отсутствующего пользователя.
        Что передаём: profile_overview_use_case.execute бросает NotFoundError.
        Что ожидаем: результат failure со статусом 404 без обращения к repo.
        """
        profile_use_case = AsyncMock()
        profile_use_case.execute.side_effect = NotFoundError("missing")
        user_repo = self._user_repository(is_following=True)
        collection_repo = self._collection_repository()
        use_case = GetPublicProfileOverviewUseCase(
            FakeUnitOfWork(UserRepository=user_repo, CollectionRepository=collection_repo),
            profile_use_case,
        )

        result = await use_case.execute(PublicProfileQuery(profile_user_id=999))

        assert result.ok is False
        assert result.status_code == 404
        user_repo.get_follow_stats.assert_not_awaited()
        collection_repo.get_public_user_collections.assert_not_awaited()
