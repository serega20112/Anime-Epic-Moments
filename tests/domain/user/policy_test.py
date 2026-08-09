from __future__ import annotations

from backend.domain import HighlightProfileSummary
from backend.domain.user.policy import (
    build_achievement_badges,
    build_genre_affinities,
    detect_profile_mood,
)


def test_build_genre_affinities_returns_most_common_genres():
    """Проверяем, что жанровый профиль сортируется по частоте и обрезается по limit."""
    result = build_genre_affinities(
        ["Comedy", "Action", "Comedy", "Drama", "Action", "Comedy"],
        limit=2,
    )

    assert [item.name for item in result] == ["Comedy", "Action"]
    assert [item.count for item in result] == [3, 2]


def test_detect_profile_mood_prefers_dark_markers():
    """Проверяем, что mood profile определяет тёмный вайб по набору жанров и эмоций."""
    mood = detect_profile_mood(
        genres=["Drama", "Psychological", "Mystery"],
        emotions=["tense"],
    )

    assert mood.label == "Тёмный вайб"
    assert mood.emoji == "😈"


def test_build_achievement_badges_returns_progress_based_badges():
    """Проверяем, что ачивки выдаются по просмотру, хайлайтам и доминирующему вкусу."""
    badges = build_achievement_badges(
        profile_summary=HighlightProfileSummary(
            highlight_count=6,
            like_count=8,
            saved_count=7,
        ),
        hours_watched=12.0,
        favorite_genres=build_genre_affinities(["Comedy", "Comedy", "Action", "Comedy"]),
        highlight_likes_received=15,
        top_mood=detect_profile_mood(genres=["Drama"], emotions=["dark"]),
    )

    codes = {item.code for item in badges}

    assert "binge_watcher" in codes
    assert "moment_hunter" in codes
    assert "collector" in codes
    assert "crowd_favorite" in codes
    assert "dark_soul" in codes
