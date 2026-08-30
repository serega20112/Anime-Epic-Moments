"""Query parameters for anime title autocomplete."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AutocompleteAnimeQuery:
    """Query parameters for anime title autocomplete.

    Attributes:
        query: Partial title text to complete.
        limit: Maximum number of suggestions to return.
        include_adult: Whether to include adult/hentai content.
    """

    query: str
    limit: int = 5
    include_adult: bool = False
