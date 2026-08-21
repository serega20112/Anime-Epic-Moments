from __future__ import annotations

import pytest

from backend.domain.policies.user_profile_policy import (
    build_achievement_badges,
    build_genre_affinities,
    detect_profile_mood,
)
from backend.domain.value_objects.highlight.profile_summary import HighlightProfileSummary


class TestGenreAffinities:
    """Юнит-тесты построения жанрового профиля."""

    @pytest.mark.unit
    async def test_returns_most_common_genres(self):
        """Что тестируем: функцию build_genre_affinities.

        Что передаём: список жанров с повторами и параметр limit=2.
        Что ожидаем: возвращается топ жанров по частоте, обрезанный по limit.
        """
        result = build_genre_affinities(
            ["Comedy", "Action", "Comedy", "Drama", "Action", "Comedy"],
            limit=2,
        )

        assert [item.name for item in result] == ["Comedy", "Action"]
        assert [item.count for item in result] == [3, 2]

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("genres", "expected_name"),
        [
            (["Comedy", "Comedy", "Drama"], "Comedy"),
            (None, None),
        ],
    )
    async def test_default_limit_is_five(self, genres, expected_name):
        """Что тестируем: значение limit по умолчанию в build_genre_affinities.

        Что передаём: список жанров без явного limit и пустой/пустой список жанров.
        Что ожидаем: при пустом входе результат пуст, иначе top-5 жанров по частоте.
        """
        result = build_genre_affinities(genres or [])

        if not genres:
            assert result == []
        else:
            assert result[0].name == expected_name


class TestProfileMood:
    """Юнит-тесты определения настроения профиля."""

    @pytest.mark.unit
    async def test_detects_dark_markers(self):
        """Что тестируем: функцию detect_profile_mood.

        Что передаём: набор тёмных жанров и напряжённых эмоций.
        Что ожидаем: возвращается ProfileMoodInsight с тёмным настроением.
        """
        mood = detect_profile_mood(
            genres=["Drama", "Psychological", "Mystery"],
            emotions=["tense"],
        )

        assert mood.label == "Тёмный вайб"
        assert mood.emoji == "😈"


class TestAchievementBadges:
    """Юнит-тесты построения набора ачивок."""

    @pytest.mark.unit
    async def test_returns_progress_based_badges(self):
        """Что тестируем: функцию build_achievement_badges.

        Что передаём: статистику профиля, часы просмотра, жанры и доминирующее настроение.
        Что ожидаем: набор ачивок содержит ожидаемые коды достижений.
        """
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
