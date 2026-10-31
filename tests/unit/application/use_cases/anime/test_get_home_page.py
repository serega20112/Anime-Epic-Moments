from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backend.application.dto.anime import HomePageQuery
from backend.application.use_cases.anime.get_home_page import CurrentSeason, GetHomePageUseCase


@pytest.mark.unit
class TestCurrentSeason:
    """Юнит-тесты значения «сезон и год»."""

    def test_stores_fields(self):
        season = CurrentSeason(2024, "winter")
        assert season.year == 2024
        assert season.season == "winter"

    def test_is_frozen(self):
        season = CurrentSeason(2024, "winter")
        with pytest.raises(Exception):
            season.season = "summer"


@pytest.mark.unit
class TestGetHomePageUseCase:
    """Юнит-тесты разрешения сезона для главной страницы."""

    async def _season(self, month: int) -> CurrentSeason:
        """Собрать сезон для даты с указанным месяцем."""
        use_case = GetHomePageUseCase()
        return await use_case.execute(HomePageQuery(moment=datetime(2025, month, 10)))

    @pytest.mark.parametrize(
        ("month", "expected"),
        [(1, "winter"), (2, "winter"), (12, "winter"), (3, "spring"), (7, "summer"), (11, "fall")],
    )
    async def test_resolves_season_from_month(self, month, expected):
        """Что тестируем: сопоставление месяца сезону аниме.
        Что передаём: дату разных месяцев одного года.
        Что ожидаем: ожидаемое название сезона и год запроса.
        """
        result = await self._season(month)

        assert result.year == 2025
        assert result.season == expected

    async def test_falls_back_to_current_time(self):
        """Что тестируем: подстановку текущего момента при пустом запросе.
        Что передаём: HomePageQuery без момента.
        Что ожидаем: корректный сезон текущего года.
        """
        result = await GetHomePageUseCase().execute(HomePageQuery())

        assert result.season in {"winter", "spring", "summer", "fall"}
        assert result.year == datetime.now(UTC).year
