"""Query parameters for fetching popular anime of a season."""

from __future__ import annotations

from dataclasses import dataclass


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
