"""Query parameters for browsing anime by Anixart-style filters."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.domain.value_objects.anime.genre_filter import GenreMatchMode


@dataclass(frozen=True, slots=True)
class FilterAnimeCatalogQuery:
    """Query parameters for browsing anime by Anixart-style filters.

    Attributes:
        genres: Genre or tag names to filter by; empty means all genres.
        genre_mode: Strategy used to combine several selected genres.
        media_type: Format filter (tv, movie, ova, ona, special) or empty.
        status: Status filter (airing, complete, upcoming) or empty.
        has_dub: When True only titles with an available voice-over are
            returned; None means the dubbing availability is not considered.
        year_from: Optional lower bound release year.
        year_to: Optional upper bound release year.
        min_score: Optional minimum normalized rating (0-10).
        sort: Sorting strategy (rating, popularity, newest, title).
        order: Sorting direction (asc, desc).
        page: One-based page number to return.
        per_page: Number of items per page.
    """

    genres: tuple[str, ...] = field(default_factory=tuple)
    genre_mode: GenreMatchMode = GenreMatchMode.ALL
    media_type: str = ""
    status: str = ""
    has_dub: bool | None = None
    year_from: int | None = None
    year_to: int | None = None
    min_score: float | None = None
    sort: str = "rating"
    order: str = "desc"
    page: int = 1
    per_page: int = 25
