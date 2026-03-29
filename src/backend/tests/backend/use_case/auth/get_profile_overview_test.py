from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

from src.backend.domain.favorite.entity import Favorite
from src.backend.domain.highlight.value_object import HighlightProfileSummary
from src.backend.domain.user.entity import User
from src.backend.use_case.auth.get_profile_overview import GetProfileOverviewUseCase


def test_get_profile_overview_use_case_builds_profile_sections(monkeypatch):
    """Проверяем, что GetProfileOverviewUseCase собирает статистику, подборки и social-активность для профиля."""
    user_repo = Mock()
    user_repo.get_by_id.return_value = User(
        id=4,
        email="user@example.com",
        username="tester",
        password_hash="hash",
        avatar_url="https://example.com/avatar.png",
        created_at=datetime(2026, 3, 20),
    )
    user_repo.get_follow_stats.return_value = (11, 6)
    highlight_repo = Mock()
    highlight_repo.get_profile_summary.return_value = HighlightProfileSummary(
        highlight_count=3,
        like_count=5,
        saved_count=7,
    )
    highlight_repo.get_by_user.return_value = [
        SimpleNamespace(anime_id=7, likes_count=9, emotion="funny"),
        SimpleNamespace(anime_id=8, likes_count=4, emotion="hype"),
    ]
    highlight_repo.get_recent_activity.return_value = [SimpleNamespace(action="like")]
    anime_client = Mock()
    anime_client.get_by_id.side_effect = lambda anime_id: {
        7: SimpleNamespace(
            title="Gintama",
            genres=["Comedy", "Action"],
            rating=8.9,
            cover_url="https://example.com/gintama.jpg",
        ),
        8: SimpleNamespace(
            title="Initial D",
            genres=["Action", "Cars"],
            rating=8.5,
            cover_url="https://example.com/initial-d.jpg",
        ),
    }.get(anime_id)
    favorite_repo = Mock()
    favorite_repo.get_by_user.return_value = [
        Favorite(
            user_id=4,
            anime_id=7,
            title="Gintama",
            genres=["Comedy", "Action"],
        )
    ]
    watch_repo = Mock()
    watch_repo.get_watched_anime_stats.return_value = [
        SimpleNamespace(anime_id=7, watched_seconds=7200.0),
        SimpleNamespace(anime_id=8, watched_seconds=3600.0),
    ]
    watch_repo.get_viewing_heatmap.return_value = [
        SimpleNamespace(date="2026-03-28", interactions=3)
    ]
    hf_client = Mock()
    hf_client.describe_taste_profile.return_value = "Тебя тянет к экшен-комедиям с хорошим темпом."
    use_case = GetProfileOverviewUseCase(
        user_repo,
        highlight_repo,
        anime_client,
        favorite_repo,
        watch_repo,
        hf_client,
    )

    use_case.recent_highlights_use_case = SimpleNamespace(
        execute=lambda **kwargs: SimpleNamespace(items=["recent-1", "recent-2", "recent-3", "recent-4", "recent-5"])
    )
    use_case.liked_highlights_use_case = SimpleNamespace(
        execute=lambda **kwargs: SimpleNamespace(items=["liked-1", "liked-2"])
    )
    use_case.saved_highlights_use_case = SimpleNamespace(
        execute=lambda **kwargs: SimpleNamespace(items=["saved-1", "saved-2"])
    )

    overview = use_case.execute(4)

    assert overview.summary.saved_count == 7
    assert overview.recent_highlights == ["recent-1", "recent-2", "recent-3", "recent-4"]
    assert overview.popular_highlights == ["recent-1", "recent-2", "recent-3", "recent-4"]
    assert overview.liked_highlights == ["liked-1", "liked-2"]
    assert overview.saved_highlights == ["saved-1", "saved-2"]
    assert overview.recent_activity[0].action == "like"
    assert overview.smart_profile.favorite_genres[0].name == "Action"
    assert overview.smart_profile.hours_watched == 3.0
    assert overview.smart_profile.top_anime[0].title == "Gintama"
    assert overview.smart_profile.ai_taste_summary == "Тебя тянет к экшен-комедиям с хорошим темпом."
    assert overview.followers_count == 11
    assert overview.following_count == 6
