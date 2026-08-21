from __future__ import annotations

import pytest

from backend.domain.value_objects.highlight.profile_summary import HighlightProfileSummary
from backend.domain.value_objects.user.profile_overview import ProfileOverview
from backend.domain.value_objects.user.smart_profile import SmartProfile
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache


def _build_overview(user_id: int, username: str):
    return ProfileOverview(
        user_id=user_id,
        email=f"{username}@example.com",
        username=username,
        avatar_url=None,
        created_at="2025-01-01",
        summary=HighlightProfileSummary(highlight_count=0, like_count=0, saved_count=0),
        recent_highlights=[],
        popular_highlights=[],
        liked_highlights=[],
        saved_highlights=[],
        recent_activity=[],
        smart_profile=SmartProfile(
            favorite_genres=[],
            dominant_mood=object(),
            average_rating=None,
            hours_watched=0.0,
            top_anime=[],
            heatmap=[],
            achievements=[],
            ai_taste_summary="",
        ),
        followers_count=0,
        following_count=0,
    )


@pytest.fixture
def overview():
    return _build_overview(7, "tester")


@pytest.fixture
def cache():
    return ProfileOverviewCache(
        store=KeyValueStore(namespace="test"),
        overview_ttl_seconds=60,
        ai_summary_ttl_seconds=120,
    )


async def test_profile_overview_cache_roundtrip_overview(cache, overview):
    assert await cache.get_overview(7) is None

    await cache.set_overview(7, overview)

    assert await cache.get_overview(7) is overview


async def test_profile_overview_cache_separates_users(cache, overview):
    other = _build_overview(8, "other")
    await cache.set_overview(7, overview)
    await cache.set_overview(8, other)

    assert await cache.get_overview(7) is overview
    assert await cache.get_overview(8) is other


async def test_profile_overview_cache_ai_summary(cache):
    assert await cache.get_ai_summary(7) is None

    await cache.set_ai_summary(7, "  loves action  ")

    assert await cache.get_ai_summary(7) == "loves action"


async def test_profile_overview_cache_invalidate_overview_keeps_summary(cache, overview):
    await cache.set_overview(7, overview)
    await cache.set_ai_summary(7, "summary")

    await cache.invalidate_overview(7)

    assert await cache.get_overview(7) is None
    assert await cache.get_ai_summary(7) == "summary"


async def test_profile_overview_cache_invalidate_user(cache, overview):
    await cache.set_overview(7, overview)
    await cache.set_ai_summary(7, "summary")

    await cache.invalidate_user(7)

    assert await cache.get_overview(7) is None
    assert await cache.get_ai_summary(7) == "summary"


async def test_profile_overview_cache_invalidate_user_with_summary(cache, overview):
    await cache.set_overview(7, overview)
    await cache.set_ai_summary(7, "summary")

    await cache.invalidate_user(7, include_ai_summary=True)

    assert await cache.get_overview(7) is None
    assert await cache.get_ai_summary(7) is None


async def test_profile_overview_does_not_leak_to_ai_summary(cache, overview):
    await cache.set_overview(7, overview)
    assert await cache.get_ai_summary(7) is None
