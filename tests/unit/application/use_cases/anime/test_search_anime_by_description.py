from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto.anime_queries import SearchAnimeByDescriptionQuery
from backend.application.use_cases.anime.search_anime_by_description import (
    SearchAnimeByDescriptionUseCase,
)
from backend.domain.anime.entity import Anime


@pytest.mark.unit
class TestSearchAnimeByDescriptionUseCase:
    """Юнит-тесты поиска аниме по естественно-языковому описанию."""

    async def test_returns_empty_result_for_blank_query(self):
        """Что тестируем: отсутствие внешних вызовов для пустого запроса.
        Что передаём: запрос из пробелов.
        Что ожидаем: пустые items, LLM не вызывается.
        """
        api_client = AsyncMock()
        llm_client = AsyncMock()
        use_case = SearchAnimeByDescriptionUseCase(api_client, llm_client)

        result = await use_case.execute(SearchAnimeByDescriptionQuery(description="   "))

        assert result.items == []
        llm_client.build_search_queries_with_meta.assert_not_awaited()

    async def test_rejects_explicit_query_with_non_adult_rating(self):
        """Что тестируем: отклонение 18+ intent при рейтинге ниже 18+.
        Что передаём: описание с adult-маркерами и age_rating=16+.
        Что ожидаем: пустые items, requires_age_confirmation=False, сообщение с 18+.
        """
        use_case = SearchAnimeByDescriptionUseCase(AsyncMock(), AsyncMock())

        result = await use_case.execute(
            SearchAnimeByDescriptionQuery(description="ищу hentai comedy", age_rating="16+")
        )

        assert result.items == []
        assert result.requires_age_confirmation is False
        assert "18+" in result.message

    async def test_requires_confirmation_for_adult_query(self):
        """Что тестируем: запрос подтверждения возраста для adult intent.
        Что передаём: описание с adult-интентом, age_rating=18+, без подтверждения.
        Что ожидаем: requires_age_confirmation=True.
        """
        use_case = SearchAnimeByDescriptionUseCase(AsyncMock(), AsyncMock())

        result = await use_case.execute(
            SearchAnimeByDescriptionQuery(
                description="ищу ecchi comedy",
                age_rating="18+",
                adult_confirmed=False,
            )
        )

        assert result.items == []
        assert result.requires_age_confirmation is True

    async def test_merges_unique_results_and_filters_nsfw(self, anime_factory):
        """Что тестируем: объединение выдач без дублей и фильтрацию NSFW.
        Что передаём: LLM-запросы и side_effect на api_client.
        Что ожидаем: все названия идут в ожидаемом порядке без дублей и NSFW.
        """
        api_client = AsyncMock()
        llm_client = AsyncMock()
        llm_client.build_search_queries_with_meta.return_value = (
            ["Gintama", "samurai comedy"],
            "hf_llm_text",
            None,
        )
        api_client.search_by_title.side_effect = self._search_by_title_results(anime_factory)
        api_client.search_by_description.side_effect = self._search_by_description_results(
            anime_factory
        )
        use_case = SearchAnimeByDescriptionUseCase(api_client, llm_client)

        result = await use_case.execute(
            SearchAnimeByDescriptionQuery(
                description='ищу что-то как "Gintama"', sort_by="match", limit=5
            )
        )

        assert [item.title for item in result.items] == ["Gintama", "Daily Lives", "Sket Dance"]

    @pytest.mark.parametrize(
        ("sort_by", "expected_titles"),
        [
            ("rating", ["High Rated", "Low Rated"]),
            ("year", ["New Title", "Old Title"]),
        ],
    )
    async def test_supports_rating_and_year_sorting(self, sort_by, expected_titles, anime_factory):
        """Что тестируем: сортировку по рейтингу и году.
        Что передаём: список аниме и стратегию сортировки.
        Что ожидаем: упорядоченные названия.
        """
        use_case = SearchAnimeByDescriptionUseCase(AsyncMock(), AsyncMock())
        items = {
            "rating": [
                anime_factory(title="Low Rated", rating=7.0),
                anime_factory(title="High Rated", rating=9.0),
            ],
            "year": [
                anime_factory(title="Old Title", year=2000),
                anime_factory(title="New Title", year=2025),
            ],
        }[sort_by]

        ordered = await use_case._sort_results(
            items=items,
            sort_by=sort_by,
            description="comedy",
            genre_hint=None,
            llm_title_hints=[],
        )

        assert [item.title for item in ordered] == expected_titles

    def _search_by_title_results(self, anime_factory):
        async def _impl(title, include_adult, limit):
            return {
                "Gintama": [
                    anime_factory(external_id="1", title="Gintama", rating=8.9),
                    anime_factory(external_id="1", title="Gintama Duplicate", rating=7.0),
                ],
                "samurai comedy": [anime_factory(external_id="2", title="Daily Lives", rating=8.1)],
            }.get(title, [])

        return _impl

    def _search_by_description_results(self, anime_factory):
        async def _impl(description, **kwargs):
            return {
                'ищу что-то как "Gintama"': [
                    Anime(
                        external_id="3",
                        title="Explicit Show",
                        description="explicit ecchi story",
                        genres=["Comedy"],
                        rating=9.0,
                    )
                ],
                "Gintama": [anime_factory(external_id="1", title="Gintama", rating=8.9)],
                "samurai comedy": [anime_factory(external_id="4", title="Sket Dance", rating=8.0)],
            }.get(description, [])

        return _impl
