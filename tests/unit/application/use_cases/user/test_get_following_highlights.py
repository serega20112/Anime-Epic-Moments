from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.application.use_cases.user.get_following_highlights import (
    GetFollowingHighlightsUseCase,
)


@pytest.mark.parametrize("sort_by", ["recent", "popular"])
def test_get_following_highlights_use_case_builds_feed_with_followed_users(sort_by):
    """Проверяем, что GetFollowingHighlightsUseCase возвращает карточки хайлайтов подписок и превью авторов."""
    repo = Mock()
    repo.get_by_users.return_value = [
        SimpleNamespace(
            id=101,
            user_id=7,
            anime_id=18,
            episode=2,
            start_timestamp=15.0,
            end_timestamp=40.0,
            title="Эпичный старт",
            category="бой",
            description="Очень мощный момент",
            is_spoiler=False,
            emotion="hype",
            created_at=datetime.utcnow() - timedelta(hours=2),
            likes_count=12,
            views_count=44,
        )
    ]
    repo.get_engagement_map.return_value = {
        101: SimpleNamespace(comments_count=3, is_liked=False, is_saved=False)
    }
    anime_api_client = Mock()
    anime_api_client.get_by_id.return_value = SimpleNamespace(
        title="Gintama",
        cover_url="https://example.com/gintama.jpg",
        external_id="18",
    )
    user_repo = Mock()
    user_repo.get_followed_users.return_value = [
        SimpleNamespace(id=7, username="creator", avatar_url="https://example.com/creator.png")
    ]
    user_repo.get_follow_stats.return_value = (0, 1)
    user_repo.get_by_ids.return_value = [
        SimpleNamespace(id=7, username="creator", avatar_url="https://example.com/creator.png")
    ]
    use_case = GetFollowingHighlightsUseCase(repo, anime_api_client, user_repo)

    page = use_case.execute(
        follower_user_id=3,
        sort_by=sort_by,
        include_spoilers=False,
    )

    assert page.total_following == 1
    assert page.followed_users[0].username == "creator"
    assert page.dashboard.items[0].owner_username == "creator"
    assert page.dashboard.items[0].owner_profile_url == "/users/7"
