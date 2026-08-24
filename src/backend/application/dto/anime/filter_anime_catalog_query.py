"""Query parameters for browsing anime by Anixart-style filters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FilterAnimeCatalogQuery:
    """Query parameters for browsing anime by Anixart-style filters.

    Attributes:
        genre: Comma-separated genre/tag names or empty for all.
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
