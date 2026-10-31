from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

import backend.application.use_cases.anime.get_season_popular as module
from backend.application.dto.anime import GetSeasonPopularQuery
from backend.application.use_cases.anime.get_season_popular import GetSeasonPopularUseCase
from backend.domain.exceptions import ValidationError
from backend.domain.policies.anime_season_policy import VALID_SEASONS, season_of


@pytest.mark.unit
class TestGetSeasonPopularUseCase:
    """Юнит-тесты сценария популярного аниме сезона."""

    def test_all_seasons_are_valid(self):
        """Что тестируем: набор поддерживаемых сезонов.
        Что передаём: ничего.
        Что ожидаем: четыре сезона аниме-нумерации.
        """
        assert VALID_SEASONS == frozenset({"winter", "spring", "summer", "fall"})

    @pytest.mark.parametrize(
        ("month", "expected"),
        [(1, "winter"), (4, "spring"), (7, "summer"), (10, "fall"), (12, "winter")],
    )
    def test_detects_season_by_month(self, month, expected):
        """Что тестируем: привязку месяца к названию сезона.
        Что передаём: дату с заданным месяцем.
        Что ожидаем: ожидаемое имя сезона.
        """
        assert season_of(datetime(2026, month, 15)) == expected

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
        """Что тестируем: подстановку текущих года и сезона при отсутствии значений.
        Что передаём: комбинации year/season/limit.
        Что ожидаем: клиент каталога вызван с ожидаемыми параметрами.
        """
        monkeypatch.setattr(module, "datetime", _FrozenDateTime(2026, 4, 1))
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
        Что ожидаем: ValidationError с русским текстом.
        """
        api_client = AsyncMock()
        use_case = GetSeasonPopularUseCase(api_client)

        with pytest.raises(ValidationError, match="Недопустимый сезон"):
            await use_case.execute(GetSeasonPopularQuery(year=2026, season=season))

        api_client.get_season_popular.assert_not_awaited()


class _FrozenDateTime(datetime):
    """Дата с зафиксированным «текущим» моментом для детерминированных тестов."""

    @classmethod
    def now(cls, tz=None) -> datetime:
        """Вернуть заранее заданный момент вместо реального текущего времени.

        Args:
            tz: Необязательная часовая зона, игнорируется двойником.

        Returns:
            datetime: Зафиксированная дата.
        """
        return datetime(2026, 4, 1)
