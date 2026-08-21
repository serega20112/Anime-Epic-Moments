from __future__ import annotations

from dataclasses import asdict

import pytest

from backend.domain.value_objects.highlight.cards import HighlightCard
from backend.domain.value_objects.highlight.profile_summary import (
    HighlightActivityItem,
    HighlightProfileSummary,
)
from backend.domain.value_objects.user.pending_email_verification import PendingEmailVerification
from backend.domain.value_objects.user.profile_overview import ProfileOverview
from backend.domain.value_objects.user.smart_profile import (
    AchievementBadge,
    GenreAffinity,
    ProfileMoodInsight,
    SmartProfile,
    TopAnimeEntry,
    ViewingHeatmapCell,
)


def _make_highlight_card():
    """Собирает готовую HighlightCard для наполнения обзора профиля."""
    return HighlightCard(
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


class TestProfileOverviewValueObject:
    """Юнит-тесты value object обзора профиля."""

    @pytest.mark.unit
    def test_profile_overview_value_object_stores_profile_sections(self):
        """Что тестируем: ProfileOverview и вложенные value objects.

        Что передаём: секции профиля, статистику, карточки хайлайтов и smart-профиль со всеми полями.
        Что ожидаем: asdict возвращает словарь, где сохранены сводка, активность, жанры и ачивки.
        """
        card = _make_highlight_card()
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
            smart_profile=SmartProfile(
                favorite_genres=[GenreAffinity(name="Comedy", count=3)],
                dominant_mood=ProfileMoodInsight(
                    label="Уютный режим",
                    description="Ты любишь теплые тайтлы.",
                    emoji="✨",
                ),
                average_rating=8.7,
                hours_watched=14.5,
                top_anime=[
                    TopAnimeEntry(
                        anime_id=7,
                        title="Gintama",
                        cover_url=None,
                        rating=8.9,
                        weight=12.4,
                    )
                ],
                heatmap=[ViewingHeatmapCell(date="2026-03-28", interactions=3)],
                achievements=[
                    AchievementBadge(
                        code="moment_hunter",
                        title="Охотник за моментами",
                        description="Делаешь хайлайты регулярно.",
                        icon="🎬",
                        rarity="epic",
                    )
                ],
                ai_taste_summary="Тебя тянет к теплой комедии и длинным марафонам.",
            ),
        )

        payload = asdict(overview)

        assert payload["summary"]["saved_count"] == 6
        assert payload["popular_highlights"][0]["likes_count"] == 5
        assert payload["recent_activity"][0]["actor_username"] == "viewer"
        assert payload["smart_profile"]["favorite_genres"][0]["name"] == "Comedy"
        assert payload["smart_profile"]["achievements"][0]["rarity"] == "epic"


class TestPendingEmailVerificationValueObject:
    """Юнит-тесты value object регистрации по email."""

    @pytest.mark.unit
    def test_pending_email_verification_value_object_stores_registration_payload(self):
        """Что тестируем: PendingEmailVerification.

        Что передаём: email, username, хеш пароля и одноразовый код подтверждения.
        Что ожидаем: asdict возвращает все переданные поля без изменений.
        """
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
