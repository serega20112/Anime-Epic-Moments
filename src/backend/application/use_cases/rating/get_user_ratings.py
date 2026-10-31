"""Сценарий чтения оценок аниме пользователя."""

from __future__ import annotations

from backend.application.dto.rating.get_user_ratings_query import GetUserRatingsQuery
from backend.application.interface.repositories.rating_repository import RatingRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain import UserAnimeRating


class GetUserRatingsUseCase:
    """Возвращает оценки пользователя по аниме."""

    def __init__(self, uow: UnitOfWorkInterface) -> None:
        """Собрать сценарий чтения оценок.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
        """
        self._uow = uow

    async def execute(self, query: GetUserRatingsQuery) -> list[UserAnimeRating]:
        """Вернуть оценки пользователя.

        Args:
            query: Запрос с идентификатором пользователя.

        Returns:
            list[UserAnimeRating]: Оценки пользователя.
        """
        async with self._uow as uow:
            return await uow.repository(RatingRepository).get_by_user(query.user_id)
