"""Идентификаторы избранного пользователя."""

from __future__ import annotations

from backend.application.dto.favorite.get_favorite_ids_query import GetFavoriteIdsQuery
from backend.application.interface.repositories.favorite_repository import FavoriteRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface


class GetFavoriteIdsUseCase:
    """Возвращает id избранных аниме пользователя (без внешних запросов)."""

    def __init__(self, uow: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий получения id избранного.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
        """
        self._uow = uow

    async def execute(self, query: GetFavoriteIdsQuery) -> list[int]:
        """Возвращает идентификаторы избранных аниме пользователя.

        Args:
            query: Запрос с идентификатором пользователя.

        Returns:
            list[int]: Идентификаторы аниме из избранного.
        """
        async with self._uow as uow:
            return await uow.repository(FavoriteRepository).get_favorite_ids(query.user_id)
