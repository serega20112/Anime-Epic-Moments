from __future__ import annotations

from dataclasses import asdict

from src.backend.domain.highlight.value_object import HighlightActivityItem, HighlightCard, HighlightProfileSummary
from src.backend.domain.user.value_object import PendingEmailVerification, ProfileOverview


def test_profile_overview_value_object_stores_profile_sections():
    """Проверяем, что ProfileOverview хранит секции профиля и social-статистику пользователя."""
    card = HighlightCard(
        id=1,
        anime_id=7,
        anime_title="Gintama",
        anime_cover=None,
        title="Лучший момент",
        category="комедия",
        episode=3,
        start_timestamp="00:10",
        end_timestamp="00:30",
        duration_seconds=20.0,
        description="desc",
        is_spoiler=False,
        emotion="funny",
        created_at="2026-03-28",
        likes_count=5,
        views_count=12,
        comments_count=3,
        is_liked=True,
        is_saved=True,
        watch_url="/watch/7?episode=3",
        share_url="/highlights/share/1",
    )
    overview = ProfileOverview(
        user_id=1,
        email="user@example.com",
        username="tester",
        avatar_url="https://example.com/avatar.png",
        created_at="2026-03-20",
        summary=HighlightProfileSummary(highlight_count=4, like_count=5, saved_count=6),
        recent_highlights=[card],
        popular_highlights=[card],
        liked_highlights=[card],
        saved_highlights=[card],
        recent_activity=[
            HighlightActivityItem(
                action="like",
                actor_user_id=2,
                actor_username="viewer",
                highlight_id=1,
                highlight_title="Лучший момент",
                created_at="2026-03-28 12:00",
            )
        ],
    )

    payload = asdict(overview)

    assert payload["summary"]["saved_count"] == 6
    assert payload["popular_highlights"][0]["likes_count"] == 5
    assert payload["recent_activity"][0]["actor_username"] == "viewer"


def test_pending_email_verification_value_object_stores_registration_payload():
    """Проверяем, что PendingEmailVerification хранит email, username, хеш пароля и одноразовый код."""
    payload = PendingEmailVerification(
        email="user@example.com",
        username="tester",
        password_hash="hashed-password",
        code="123456",
        theme="dark",
    )

    serialized = asdict(payload)

    assert serialized == {
        "email": "user@example.com",
        "username": "tester",
        "password_hash": "hashed-password",
        "code": "123456",
        "theme": "dark",
    }
