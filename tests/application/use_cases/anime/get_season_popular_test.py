from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

import pytest

from backend.application.use_cases import GetSeasonPopularUseCase
from backend.application.use_cases import get_season_popular as get_season_popular_module


@pytest.mark.parametrize(
    ("month", "expected"),
    [(1, "winter"), (4, "spring"), (7, "summer"), (10, "fall")],
)
def test_get_season_popular_detects_current_season(monkeypatch, month, expected):
    """Проверяем, что GetSeasonPopularUseCase определяет сезон по текущему месяцу."""
    fake_datetime = type(
        "FakeDateTime",
        (),
        {"now": staticmethod(lambda: datetime(2026, month, 1))},
    )
    monkeypatch.setattr(get_season_popular_module, "datetime", fake_datetime)
    use_case = GetSeasonPopularUseCase(Mock())

    assert use_case._current_season() == expected


def test_get_season_popular_uses_current_year_and_season_by_default(anime_factory, monkeypatch):
    """Проверяем, что GetSeasonPopularUseCase подставляет текущие год и сезон, если они не переданы."""
    fake_datetime = type(
        "FakeDateTime",
        (),
        {"now": staticmethod(lambda: datetime(2026, 4, 1))},
    )
    monkeypatch.setattr(get_season_popular_module, "datetime", fake_datetime)
    api_client = Mock()
    api_client.get_season_popular.return_value = [anime_factory(title="Season Hit")]
    use_case = GetSeasonPopularUseCase(api_client)

    result = use_case.execute(limit=4)

    assert [item.title for item in result] == ["Season Hit"]
    api_client.get_season_popular.assert_called_once_with(year=2026, season="spring", limit=4)
