from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.user.get_public_profile_overview import (
    GetPublicProfileOverviewUseCase,
)
from backend.domain import HighlightProfileSummary, SmartProfile
from backend.domain.user.value_object import ProfileMoodInsight


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

    @pytest.mark.parametrize(
        ("viewer_user_id", "is_following", "can_follow"),
        [
            (None, False, False),
            (5, True, True),
        ],
    )
    async def test_builds_public_payload(self, viewer_user_id, is_following, can_follow):
        """Что тестируем: сборку публичного профиля с social-статистикой.
        Что передаём: viewer_user_id и ответ is_following.
        Что ожидаем: профиль и его поля собраны корректно.
        """
        profile_use_case = AsyncMock()
        profile_use_case.execute.return_value = self._profile_payload()
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
        use_case = GetPublicProfileOverviewUseCase(profile_use_case, user_repo, collection_repo)

        result = await use_case.execute(profile_user_id=7, viewer_user_id=viewer_user_id)

        assert result.ok is True
        data = result.data
        assert data.profile.username == "public-user"
        assert data.followers_count == 3
        assert data.following_count == 2
        assert data.is_following is is_following
        assert data.can_follow is can_follow
        assert data.public_collections[0].title == "Ночная подборка"
        assert data.followers_preview[0].profile_url == "/users/11"
        assert data.following_preview[0].profile_url == "/users/12"

    async def test_returns_failure_when_profile_use_case_raises_value_error(self):
        """Что тестируем: обработку отсутствующего пользователя.
        Что передаём: profile_overview_use_case.execute бросает ValueError.
        Что ожидаем: результат failure со статусом 404 без обращения к repo.
        """
        profile_use_case = AsyncMock()
        profile_use_case.execute.side_effect = ValueError("missing")
        user_repo = AsyncMock()
        collection_repo = AsyncMock()
        use_case = GetPublicProfileOverviewUseCase(profile_use_case, user_repo, collection_repo)

        result = await use_case.execute(profile_user_id=999, viewer_user_id=None)

        assert result.ok is False
        assert result.status_code == 404
        user_repo.get_follow_stats.assert_not_awaited()
