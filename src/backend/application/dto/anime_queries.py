"""Data transfer objects for anime search and discovery queries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SearchAnimeQuery:
    """Query parameters for searching anime by title.

    Attributes:
        title: Search title text.
        limit: Maximum number of results to return.
    """

    title: str
    limit: int = 10


@dataclass(frozen=True, slots=True)
class SearchAnimeByDescriptionQuery:
    """Query parameters for searching anime by natural language description.

    Attributes:
        description: Free-form description text.
        genre_hint: Optional genre hint to narrow the search.
        year_from: Optional lower bound for release year.
        year_to: Optional upper bound for release year.
        min_rating: Optional minimum rating threshold.
        age_rating: Age rating filter (all, 12+, 16+, 18+).
        adult_confirmed: Whether the user confirmed adult content access.
        sort_by: Sorting strategy (match, rating, year).
        limit: Maximum number of results to return.
    """

    description: str
    genre_hint: str | None = None
    year_from: int | None = None
    year_to: int | None = None
    min_rating: int | None = None
    age_rating: str = "all"
    adult_confirmed: bool = False
    sort_by: str = "match"
    limit: int = 10


@dataclass(frozen=True, slots=True)
class AutocompleteAnimeQuery:
    """Query parameters for anime title autocomplete.

    Attributes:
        query: Partial title text to complete.
        limit: Maximum number of suggestions to return.
    """

    query: str
    limit: int = 5


@dataclass(frozen=True, slots=True)
class GetSeasonPopularQuery:
    """Query parameters for fetching popular anime of a season.

    Attributes:
        year: Season year.
        season: Season name (winter, spring, summer, fall).
        limit: Maximum number of results to return.
    """

    year: int
    season: str
    limit: int = 10


@dataclass(frozen=True, slots=True)
class FilterAnimeCatalogQuery:
    """Query parameters for browsing anime by Anixart-style filters.

    Attributes:
        genre: Selected genre name or empty for all.
        media_type: Format filter (tv, movie, ova, ona, special) or empty.
        status: Status filter (airing, complete, upcoming) or empty.
        year_from: Optional lower bound release year.
        year_to: Optional upper bound release year.
        min_score: Optional minimum normalized rating (0-10).
        sort: Sorting strategy (rating, popularity, newest, title).
        order: Sorting direction (asc, desc).
        limit: Maximum number of results to return.
    """

    genre: str = ""
    media_type: str = ""
    status: str = ""
    year_from: int | None = None
    year_to: int | None = None
    min_score: float | None = None
    sort: str = "rating"
    order: str = "desc"
    limit: int = 30
