from __future__ import annotations

import pytest

from backend.domain.recommendation.value_object import RecommendationResult


class TestRecommendationResult:
    """Юнит-тесты value object результата рекомендации."""

    @pytest.mark.unit
    def test_uses_empty_genres_by_default(self):
        """Что тестируем: конструктор RecommendationResult при минимальном наборе полей.

        Что передаём: рекомендацию без genres и watch_url.
        Что ожидаем: genres становится пустым списком, watch_url равен None.
        """
        result = RecommendationResult(
            anime_id=1,
            reason="genre match",
            similarity_score=0.9,
            title="Gintama",
            description="Comedy",
            image_url=None,
        )

        assert result.genres == []
        assert result.watch_url is None

    @pytest.mark.unit
    def test_preserves_explicit_fields(self):
        """Что тестируем: конструктор RecommendationResult при передаче всех полей.

        Что передаём: рекомендацию с жанрами, URL картинки и watch_url.
        Что ожидаем: все переданные поля сохраняются корректно.
        """
        result = RecommendationResult(
            anime_id=2,
            reason="favorite overlap",
            similarity_score=0.75,
            title="Initial D",
            description="Racing",
            image_url="https://example.com/initial-d.jpg",
            genres=["Action", "Cars"],
            watch_url="/watch/2",
        )

        assert result.title == "Initial D"
        assert result.genres == ["Action", "Cars"]
        assert result.watch_url == "/watch/2"
