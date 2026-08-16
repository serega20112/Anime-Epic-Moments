from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import AskAiRecommendationsCommand
from backend.application.use_cases.recommendation.ask_ai_recommendations import (
    AskAiRecommendationsUseCase,
)


@pytest.mark.unit
class TestAskAiRecommendationsUseCase:
    """Юнит-тесты подбора AI-рекомендаций по текстовому запросу."""

    async def test_returns_ranked_items_from_ai_queries(self):
        """Что тестируем: преобразование запроса в рекомендации и исключение избранного.
        Что передаём: favorite_repo с одним favorite и side_effect на api_client.
        Что ожидаем: recommendations отсортированы, без дублей и без favorite.
        """
        favorite_repo = AsyncMock()
        favorite_repo.get_by_user.return_value = [
            SimpleNamespace(anime_id=1, genres=["Action", "Comedy"])
        ]
        anime_api_client = AsyncMock()
        anime_api_client.search_by_description.side_effect = [
            [],
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
            [],
        ]
        anime_api_client.search_by_title.return_value = []
        hf_client = AsyncMock()
        hf_client.build_search_queries_with_meta.return_value = (
            ["dark naruto", "tragic shounen"],
            "hf_llm_text",
            None,
        )
        use_case = AskAiRecommendationsUseCase(favorite_repo, anime_api_client, hf_client)

        result = await use_case.execute(
            AskAiRecommendationsCommand(user_id=7, query="что-то как Naruto, но темнее", limit=3)
        )

        assert result.ok is True
        items = result.data
        assert [item.anime_id for item in items] == [2, 3]
        assert "AI" in items[0].reason
        assert items[0].watch_url == "/watch/2?episode=1"

    async def test_returns_failure_for_blank_query(self):
        """Что тестируем: отказ при пустом запросе.
        Что передаём: query из пробелов.
        Что ожидаем: результат failure со статусом 400.
        """
        favorite_repo = AsyncMock()
        use_case = AskAiRecommendationsUseCase(favorite_repo, AsyncMock(), AsyncMock())

        result = await use_case.execute(
            AskAiRecommendationsCommand(user_id=7, query="   ", limit=3)
        )

        assert result.ok is False
        assert result.status_code == 400

    async def test_prioritizes_explicit_topic_over_profile_bias(self):
        """Что тестируем: явная тема запроса удерживает рекомендации в нужной области.
        Что передаём: запрос про котиков и кандидатов, включая нерелевантный спорт.
        Что ожидаем: остается только релевантный по теме кандидат.
        """
        favorite_repo = AsyncMock()
        favorite_repo.get_by_user.return_value = [
            SimpleNamespace(anime_id=10, genres=["Sports", "Comedy"])
        ]
        anime_api_client = AsyncMock()
        anime_api_client.search_by_description.side_effect = [
            [],
            [
                SimpleNamespace(
                    external_id="20",
                    title="Chi's Sweet Home",
                    description="A small kitten finds a new family and other cats.",
                    cover_url="cover-20",
                    genres=["Slice of Life", "Comedy"],
                    rating=8.2,
                ),
                SimpleNamespace(
                    external_id="21",
                    title="Slam Dunk",
                    description="A basketball team fights for the top.",
                    cover_url="cover-21",
                    genres=["Sports", "Comedy"],
                    rating=9.0,
                ),
            ],
            [],
        ]
        anime_api_client.search_by_title.return_value = []
        hf_client = AsyncMock()
        hf_client.build_search_queries_with_meta.return_value = (
            ["cat anime", "cute cats"],
            "hf_llm_text",
            None,
        )
        use_case = AskAiRecommendationsUseCase(favorite_repo, anime_api_client, hf_client)

        result = await use_case.execute(
            AskAiRecommendationsCommand(user_id=9, query="аниме про котиков", limit=3)
        )

        assert result.ok is True
        assert [item.anime_id for item in result.data] == [20]
        assert "смыслу запроса" in result.data[0].reason
