from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

from backend.application.use_cases import GetProfileOverviewUseCase
from backend.domain import Favorite
from backend.domain import HighlightProfileSummary
from backend.domain import User
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache


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


def test_get_profile_overview_use_case_uses_cached_overview_and_ai_summary():
    """Проверяем, что GetProfileOverviewUseCase берет overview и AI summary из кэша без повторного тяжелого вызова."""
    cache = ProfileOverviewCache(
        store=KeyValueStore(redis_url=None, namespace="test-profile-overview"),
        overview_ttl_seconds=180,
        ai_summary_ttl_seconds=1800,
    )
    user_repo = Mock()
    user_repo.get_by_id.return_value = User(
        id=4,
        email="user@example.com",
        username="tester",
        password_hash="hash",
        created_at=datetime(2026, 3, 20),
    )
    user_repo.get_follow_stats.return_value = (11, 6)
    highlight_repo = Mock()
    highlight_repo.get_profile_summary.return_value = HighlightProfileSummary(
        highlight_count=1,
        like_count=2,
        saved_count=3,
    )
    highlight_repo.get_by_user.return_value = [
        SimpleNamespace(anime_id=7, likes_count=2, emotion="funny"),
    ]
    highlight_repo.get_recent_activity.return_value = [SimpleNamespace(action="like")]
    anime_client = Mock()
    anime_client.get_by_id.return_value = SimpleNamespace(
        title="Gintama",
        genres=["Comedy", "Action"],
        rating=8.9,
        cover_url="https://example.com/gintama.jpg",
    )
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
    ]
    watch_repo.get_viewing_heatmap.return_value = [
        SimpleNamespace(date="2026-03-28", interactions=3)
    ]
    hf_client = Mock()
    hf_client.describe_taste_profile.return_value = "Кэшируемый AI summary."
    use_case = GetProfileOverviewUseCase(
        user_repo,
        highlight_repo,
        anime_client,
        favorite_repo,
        watch_repo,
        hf_client,
        cache,
    )
    use_case.recent_highlights_use_case = SimpleNamespace(
        execute=lambda **kwargs: SimpleNamespace(items=["recent-1"])
    )
    use_case.liked_highlights_use_case = SimpleNamespace(
        execute=lambda **kwargs: SimpleNamespace(items=["liked-1"])
    )
    use_case.saved_highlights_use_case = SimpleNamespace(
        execute=lambda **kwargs: SimpleNamespace(items=["saved-1"])
    )

    first = use_case.execute(4)

    user_repo.get_by_id.reset_mock()
    hf_client.describe_taste_profile.reset_mock()
    second = use_case.execute(4)

    assert first.smart_profile.ai_taste_summary == "Кэшируемый AI summary."
    assert second.smart_profile.ai_taste_summary == "Кэшируемый AI summary."
    user_repo.get_by_id.assert_not_called()
    hf_client.describe_taste_profile.assert_not_called()

    cache.invalidate_overview(4)
    user_repo.get_by_id.reset_mock()
    third = use_case.execute(4)

    assert third.smart_profile.ai_taste_summary == "Кэшируемый AI summary."
    hf_client.describe_taste_profile.assert_not_called()
