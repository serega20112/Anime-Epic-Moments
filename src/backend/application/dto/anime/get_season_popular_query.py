"""Параметры запроса популярного аниме за сезон."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetSeasonPopularQuery:
    """Параметры запроса популярного аниме за сезон.

    Attributes:
        year: Год сезона.
        season: Название сезона: зима, весна, лето или осень.
        limit: Максимальное число результатов.
    """

    year: int
    season: str
    limit: int = 10
