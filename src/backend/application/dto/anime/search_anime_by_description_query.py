"""Query parameters for searching anime by natural language description."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SearchAnimeByDescriptionQuery:
    """Query parameters for searching anime by natural language description.

    Attributes:
        description: Free-form description text.
        genre_hint: Optional genre hint to narrow the search.
        year_from: Optional lower bound for release year.
        year_to: Optional upper bound for release year.
        min_rating: Optional minimum rating threshold.
        age_rating: Age rating filter (all, 6+, 12+, 16+, 18+).
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
