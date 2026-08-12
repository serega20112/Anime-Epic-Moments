from __future__ import annotations

from datetime import datetime

from backend.application.use_cases.anime.get_home_page import CurrentSeason, GetHomePageUseCase


class TestCurrentSeason:
    def test_stores_fields(self):
        season = CurrentSeason(2024, "winter")
        assert season.year == 2024
        assert season.season == "winter"


class TestGetHomePageUseCase:
    def _season(self, *args, **kwargs):
        return GetHomePageUseCase().execute(now=datetime(*args, **kwargs))

    def test_winter_from_december(self):
        result = self._season(2024, 12, 15)
        assert result.year == 2024
        assert result.season == "winter"

    def test_winter_from_january(self):
        result = self._season(2025, 1, 10)
        assert result.year == 2025
        assert result.season == "winter"

    def test_winter_from_february(self):
        assert self._season(2025, 2, 1).season == "winter"

    def test_spring(self):
        assert self._season(2025, 3, 1).season == "spring"
        assert self._season(2025, 5, 31).season == "spring"

    def test_summer(self):
        assert self._season(2025, 6, 1).season == "summer"
        assert self._season(2025, 8, 31).season == "summer"

    def test_fall(self):
        assert self._season(2025, 9, 1).season == "fall"
        assert self._season(2025, 11, 30).season == "fall"