from __future__ import annotations

import pytest

from backend.application.dto.anime_queries import (
    AutocompleteAnimeQuery,
    GetSeasonPopularQuery,
    SearchAnimeByDescriptionQuery,
    SearchAnimeQuery,
)


class TestSearchAnimeQuery:
    def test_stores_required_fields(self):
        query = SearchAnimeQuery(title="Naruto", limit=25)
        assert query.title == "Naruto"
        assert query.limit == 25

    def test_default_limit(self):
        assert SearchAnimeQuery(title="Bleach").limit == 10

    def test_is_frozen(self):
        query = SearchAnimeQuery(title="One Piece")
        with pytest.raises(Exception):
            query.title = "EDITED"


class TestSearchAnimeByDescriptionQuery:
    def test_stores_fields_and_defaults(self):
        query = SearchAnimeByDescriptionQuery(description="a hero wields a giant sword")
        assert query.description == "a hero wields a giant sword"
        assert query.genre_hint is None
        assert query.year_from is None
        assert query.year_to is None
        assert query.min_rating is None
        assert query.age_rating == "all"
        assert query.adult_confirmed is False
        assert query.sort_by == "match"
        assert query.limit == 10

    def test_stores_overridden_filters(self):
        query = SearchAnimeByDescriptionQuery(
            description="sci-fi",
            genre_hint="Mecha",
            year_from=1995,
            year_to=2010,
            min_rating=8,
            age_rating="16+",
            adult_confirmed=True,
            sort_by="rating",
            limit=5,
        )
        assert query.genre_hint == "Mecha"
        assert query.year_from == 1995
        assert query.year_to == 2010
        assert query.min_rating == 8
        assert query.age_rating == "16+"
        assert query.adult_confirmed is True
        assert query.sort_by == "rating"
        assert query.limit == 5


class TestAutocompleteAnimeQuery:
    def test_stores_fields(self):
        query = AutocompleteAnimeQuery(query="Fate", limit=8)
        assert query.query == "Fate"
        assert query.limit == 8

    def test_default_limit(self):
        assert AutocompleteAnimeQuery(query="Fate").limit == 5


class TestGetSeasonPopularQuery:
    def test_stores_fields(self):
        query = GetSeasonPopularQuery(year=2024, season="winter", limit=15)
        assert query.year == 2024
        assert query.season == "winter"
        assert query.limit == 15

    def test_default_limit(self):
        query = GetSeasonPopularQuery(year=2024, season="fall")
        assert query.limit == 10