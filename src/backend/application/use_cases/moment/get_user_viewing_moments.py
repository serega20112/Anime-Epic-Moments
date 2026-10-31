"""Сценарий списка черновиков моментов просмотра."""

from backend.application.dto.moment.get_user_viewing_moments_query import (
    GetUserViewingMomentsQuery,
)
from backend.application.interface.repositories.moment_repository import MomentRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult


class GetUserViewingMomentsUseCase:
    """Возвращает черновики моментов пользователя."""

    def __init__(self, uow: UnitOfWorkInterface) -> None:
        """Собрать сценарий списка черновиков.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
        """
        self._uow = uow

    async def execute(self, query: GetUserViewingMomentsQuery) -> UseCaseResult:
        """Получить черновики моментов пользователя.

        Args:
            query: Запрос с идентификатором владельца черновиков.

        Returns:
            UseCaseResult: Результат со списком моментов.
        """
        async with self._uow as uow:
            moments = await uow.repository(MomentRepository).get_moments_by_user(query.user_id)
        return UseCaseResult.success(moments)
