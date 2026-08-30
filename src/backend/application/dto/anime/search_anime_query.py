"""Query parameters for searching anime by title."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SearchAnimeQuery:
    """Query parameters for searching anime by title.

    Attributes:
        title: Search title text.
        limit: Maximum number of results to return.
        include_adult: Whether to include adult/hentai content.
    """

    title: str
    limit: int = 10
    include_adult: bool = False
