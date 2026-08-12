from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from backend.application.dto.anime_queries import GetSeasonPopularQuery
from backend.application.use_cases.anime.get_season_popular import (
    GetSeasonPopularUseCase,
    _VALID_SEASONS,
)
from backend.domain.exceptions import ValidationError

import backend.application.use_cases.anime.get_season_popular as module


@pytest.mark.unit
class TestGetSeasonPopularUseCase:
    """Юнит-тесты сценария получения популярного аниме сезона."""

    @pytest.mark.parametrize(
        ("month", "expected"),
        [(1, "winter"), (4, "spring"), (7, "summer"), (10, "fall")],
    )
    def test_detects_current_season(self, monkeypatch, month, expected):
        """Что тестируем: определение сезона по текущему месяцу.
        Что передаём: подмененное datetime с заданным месяцем.
        Что ожидаем: соответствие имени сезона месяцу.
        """
        fake_datetime = type(
            "FakeDateTime",
            (),
            {"now": staticmethod(lambda: datetime(2026, month, 1))},
        )
        monkeypatch.setattr(module, "datetime", fake_datetime)
        use_case = GetSeasonPopularUseCase(Mock())

        assert use_case._current_season() == expected

    def test_all_seasons_are_valid(self):
        """Что тестируем: список поддерживаемых сезонов.
        Что передаём: ничего.
        Что ожидаем: зимние/весенние/летние/осенние сезоны валидны.
        """
        assert _VALID_SEASONS == {"winter", "spring", "summer", "fall"}

    @pytest.mark.parametrize(
        ("year", "season", "limit", "expected_calls"),
        [
            (None, None, None, {"year": 2026, "season": "spring", "limit": None}),
            (2025, "winter", 10, {"year": 2025, "season": "winter", "limit": 10}),
        ],
    )
    async def test_uses_current_year_and_season_by_default(
            self, anime_factory, monkeypatch, year, season, limit, expected_calls
    ):
        """Что тестируем: подстановку текущих года и сезона если не заданы.
        Что передаём: комбинации year/season/limit.
        Что ожидаем: api_client вызывается с ожидаемыми параметрами и возвращается список.
        """
        fake_datetime = type(
            "FakeDateTime",
            (),
            {"now": staticmethod(lambda: datetime(2026, 4, 1))},
        )
        monkeypatch.setattr(module, "datetime", fake_datetime)
        api_client = AsyncMock()
        api_client.get_season_popular.return_value = [anime_factory(title="Season Hit")]
        use_case = GetSeasonPopularUseCase(api_client)

        result = await use_case.execute(
            GetSeasonPopularQuery(year=year, season=season, limit=limit)
        )

        assert [item.title for item in result] == ["Season Hit"]
        api_client.get_season_popular.assert_awaited_once_with(**expected_calls)

    @pytest.mark.parametrize("season", ["invalid", "summerX", "WINTER"])
    async def test_rejects_invalid_season(self, season):
        """Что тестируем: отказ при недопустимом имени сезона.
        Что передаём: невалидные строки сезонов.
        Что ожидаем: ValidationError.
        """
        api_client = AsyncMock()
        use_case = GetSeasonPopularUseCase(api_client)

        with pytest.raises(ValidationError):
            await use_case.execute(GetSeasonPopularQuery(year=2026, season=season))