from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.backend.domain.highlight.value_object import HighlightProfileSummary
from src.backend.domain.user.value_object import ProfileMoodInsight, SmartProfile
from src.backend.use_case.user.get_public_profile_overview import (
    GetPublicProfileOverviewUseCase,
)


@pytest.mark.parametrize(
    ("viewer_user_id", "is_following", "can_follow"),
    [
        (None, False, False),
        (5, True, True),
    ],
)
def test_get_public_profile_overview_use_case_builds_public_payload(
    viewer_user_id,
    is_following,
    can_follow,
):
    """Проверяем, что GetPublicProfileOverviewUseCase собирает публичный профиль, социальные счетчики и коллекции."""
    profile_use_case = Mock()
    profile_use_case.execute.return_value = SimpleNamespace(
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
    user_repo = Mock()
    user_repo.get_follow_stats.return_value = (3, 2)
    user_repo.get_followers.return_value = [
        SimpleNamespace(id=11, username="follower-1", avatar_url=None)
    ]
    user_repo.get_followed_users.return_value = [
        SimpleNamespace(id=12, username="followed-1", avatar_url="https://example.com/followed.png")
    ]
    user_repo.is_following.return_value = is_following
    collection_repo = Mock()
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

    result = use_case.execute(profile_user_id=7, viewer_user_id=viewer_user_id)

    assert result.profile.username == "public-user"
    assert result.followers_count == 3
    assert result.following_count == 2
    assert result.is_following is is_following
    assert result.can_follow is can_follow
    assert result.public_collections[0].title == "Ночная подборка"
    assert result.followers_preview[0].profile_url == "/users/11"
    assert result.following_preview[0].profile_url == "/users/12"
