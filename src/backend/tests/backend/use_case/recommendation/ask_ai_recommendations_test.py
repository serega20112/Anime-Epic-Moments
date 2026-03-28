from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from src.backend.use_case.recommendation.ask_ai_recommendations import (
    AskAiRecommendationsUseCase,
)


def test_ask_ai_recommendations_returns_ranked_items_from_ai_queries():
    """Проверяем, что AskAiRecommendationsUseCase преобразует текстовый запрос в рекомендации и исключает уже избранное."""
    favorite_repo = Mock()
    favorite_repo.get_by_user.return_value = [
        SimpleNamespace(anime_id=1, genres=["Action", "Comedy"])
    ]
    anime_api_client = Mock()
    anime_api_client.search_by_description.side_effect = [
        [
            SimpleNamespace(
                external_id="2",
                title="Darker Naruto",
                description="desc",
                cover_url="cover-2",
                genres=["Action", "Drama"],
                rating=9.0,
            ),
            SimpleNamespace(
                external_id="1",
                title="Naruto",
                description="desc",
                cover_url="cover-1",
                genres=["Action"],
                rating=8.0,
            ),
        ],
        [
            SimpleNamespace(
                external_id="3",
                title="Bleach",
                description="desc",
                cover_url="cover-3",
                genres=["Action", "Supernatural"],
                rating=8.5,
            )
        ],
    ]
    hf_client = Mock()
    hf_client.build_search_queries_with_meta.return_value = (
        ["dark naruto", "tragic shounen"],
        "hf_llm_text",
        None,
    )
    use_case = AskAiRecommendationsUseCase(
        favorite_repo,
        anime_api_client,
        hf_client,
    )

    result = use_case.execute(user_id=7, query="что-то как Naruto, но темнее", limit=3)

    assert [item.anime_id for item in result] == [2, 3]
    assert "AI" in result[0].reason
    assert result[0].watch_url == "/watch/2?episode=1"
