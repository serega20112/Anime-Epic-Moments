from __future__ import annotations

from unittest.mock import Mock

import pytest

from backend.application.use_cases.anime.search_anime_by_description import (
    SearchAnimeByDescriptionUseCase,
)
from backend.domain import Anime


def test_search_anime_by_description_returns_empty_result_for_blank_query():
    """Проверяем, что SearchAnimeByDescriptionUseCase не ходит во внешние зависимости для пустого запроса."""
    api_client = Mock()
    llm_client = Mock()
    use_case = SearchAnimeByDescriptionUseCase(api_client, llm_client)

    result = use_case.execute("   ")

    assert result.items == []
    llm_client.build_search_queries_with_meta.assert_not_called()


def test_search_anime_by_description_rejects_explicit_query_with_non_adult_rating():
    """Проверяем, что SearchAnimeByDescriptionUseCase отклоняет 18+ intent при рейтинге ниже 18+."""
    use_case = SearchAnimeByDescriptionUseCase(Mock(), Mock())

    result = use_case.execute("ищу hentai comedy", age_rating="16+")

    assert result.items == []
    assert result.requires_age_confirmation is False
    assert "18+" in result.message


def test_search_anime_by_description_requires_confirmation_for_adult_query():
    """Проверяем, что SearchAnimeByDescriptionUseCase просит подтверждение возраста для adult intent."""
    use_case = SearchAnimeByDescriptionUseCase(Mock(), Mock())

    result = use_case.execute("ищу ecchi comedy", age_rating="18+", adult_confirmed=False)

    assert result.items == []
    assert result.requires_age_confirmation is True


def test_search_anime_by_description_merges_unique_results_and_filters_nsfw(anime_factory):
    """Проверяем, что SearchAnimeByDescriptionUseCase объединяет выдачу без дублей и фильтрует NSFW."""
    api_client = Mock()
    llm_client = Mock()
    llm_client.build_search_queries_with_meta.return_value = (
        ["Gintama", "samurai comedy"],
        "hf_llm_text",
        None,
    )
    api_client.search_by_title.side_effect = lambda title, include_adult, limit: {
        "Gintama": [
            anime_factory(external_id="1", title="Gintama", rating=8.9),
            anime_factory(external_id="1", title="Gintama Duplicate", rating=7.0),
        ],
        "samurai comedy": [anime_factory(external_id="2", title="Daily Lives", rating=8.1)],
    }.get(title, [])
    api_client.search_by_description.side_effect = lambda description, **kwargs: {
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
    use_case = SearchAnimeByDescriptionUseCase(api_client, llm_client)

    result = use_case.execute('ищу что-то как "Gintama"', sort_by="match", limit=5)

    assert [item.title for item in result.items] == ["Gintama", "Daily Lives", "Sket Dance"]


@pytest.mark.parametrize(
    ("sort_by", "expected_titles"),
    [
        ("rating", ["High Rated", "Low Rated"]),
        ("year", ["New Title", "Old Title"]),
    ],
)
def test_search_anime_by_description_supports_rating_and_year_sorting(
        sort_by,
        expected_titles,
        anime_factory,
):
    """Проверяем, что SearchAnimeByDescriptionUseCase сортирует результаты по рейтингу и году."""
    use_case = SearchAnimeByDescriptionUseCase(Mock(), Mock())
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

    ordered = use_case._sort_results(
        items=items,
        sort_by=sort_by,
        description="comedy",
        genre_hint=None,
        llm_title_hints=[],
    )

    assert [item.title for item in ordered] == expected_titles
