"""Правила привязки даты к сезону аниме."""

from __future__ import annotations

from datetime import datetime

WINTER = "winter"
SPRING = "spring"
SUMMER = "summer"
FALL = "fall"

VALID_SEASONS = frozenset({WINTER, SPRING, SUMMER, FALL})
SEASON_BY_MONTH = {
    1: WINTER,
    2: WINTER,
    3: SPRING,
    4: SPRING,
    5: SPRING,
    6: SUMMER,
    7: SUMMER,
    8: SUMMER,
    9: FALL,
    10: FALL,
    11: FALL,
    12: WINTER,
}


def season_of(moment: datetime) -> str:
    """Вернуть название сезона аниме по месяцу даты.

    Args:
        moment: Дата, месяц которой определяет сезон.

    Returns:
        str: Одно из названий из :data:`VALID_SEASONS`.
    """
    return SEASON_BY_MONTH[int(moment.month)]
