"""Сценарий получения популярного аниме текущего сезона."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.application.dto.anime import GetSeasonPopularQuery
from backend.application.interface.services import AnimeApiClientInterface
from backend.domain.entities.anime.anime import Anime
from backend.domain.exceptions import ValidationError
from backend.domain.policies.anime_season_policy import VALID_SEASONS, season_of


class GetSeasonPopularUseCase:
    """Сценарий получения популярного аниме для заданного сезона и года."""

    def __init__(self, api_client: AnimeApiClientInterface) -> None:
        """Собрать сценарий из зависимостей.

        Args:
            api_client: Клиент API аниме.
        """
        self._api_client = api_client

    async def execute(self, query: GetSeasonPopularQuery) -> list[Anime]:
        """Вернуть популярное аниме для запрошенного сезона.

        Args:
            query: Сезон, год и размер выборки.

        Returns:
            list[Anime]: Список популярного аниме.

        Raises:
            ValidationError: Название сезона вне допустимого набора.
        """
        moment = datetime.now(UTC)
        year = query.year or moment.year
        season = query.season or season_of(moment)
        if season not in VALID_SEASONS:
            raise ValidationError(f"Недопустимый сезон: {season}")
        return await self._api_client.get_season_popular(
            year=year,
            season=season,
            limit=query.limit,
        )
