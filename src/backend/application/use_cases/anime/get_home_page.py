"""Use case for the home page: resolves the current anime season and year."""

from __future__ import annotations

from datetime import datetime


class CurrentSeason:
    """Current anime season resolved for the home page.

    Attributes:
        year: Calendar year of the season.
        season: Season name (winter, spring, summer, fall).
    """

    __slots__ = ("year", "season")

    def __init__(self, year: int, season: str):
        """Initialize the season value object.

        Args:
            year: Season year.
            season: Season name.
        """
        self.year = year
        self.season = season


class GetHomePageUseCase:
    """Build home page context including the current anime season."""

    async def execute(self, now: datetime | None = None) -> CurrentSeason:
        """Resolve the current anime season from the current month.

        Args:
            now: Fixed clock for deterministic testing. Defaults to UTC now.

        Returns:
            CurrentSeason: Current season and year.
        """
        current = now or datetime.utcnow()
        month = int(current.month)
        year = int(current.year)
        if month in {12, 1, 2}:
            return CurrentSeason(year, "winter")
        if month in {3, 4, 5}:
            return CurrentSeason(year, "spring")
        if month in {6, 7, 8}:
            return CurrentSeason(year, "summer")
        return CurrentSeason(year, "fall")
