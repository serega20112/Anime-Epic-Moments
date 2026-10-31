"""Сценарий домашней страницы: разрешает текущее время года аниме."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from backend.application.dto.anime import HomePageQuery
from backend.domain.policies.anime_season_policy import season_of


@dataclass(frozen=True, slots=True)
class CurrentSeason:
    """Текущий сезон аниме для главной страницы.

    Attributes:
        year: Год, к которому относится сезон.
        season: Название сезона по нумерации аниме-индустрии.
    """

    year: int
    season: str


class GetHomePageUseCase:
    """Сценарий подготовки домашней страницы: разрешает текущее время года аниме."""

    async def execute(self, query: HomePageQuery) -> CurrentSeason:
        """Разрешить текущее время года аниме из месяца запроса.

        Args:
            query: Момент наблюдения сезона; без значения берётся текущее UTC.

        Returns:
            CurrentSeason: Текущее время года и год.
        """
        moment = query.moment or datetime.now(UTC)
        return CurrentSeason(year=int(moment.year), season=season_of(moment))
