from __future__ import annotations

from src.backend.domain.recommendation.value_object import RecommendationResult


def test_recommendation_result_uses_empty_genres_by_default():
    """Проверяем, что RecommendationResult подставляет пустой список жанров по умолчанию."""
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


def test_recommendation_result_preserves_explicit_fields():
    """Проверяем, что RecommendationResult сохраняет переданные поля рекомендации."""
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
