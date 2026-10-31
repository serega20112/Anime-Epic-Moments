"""Удаление черновика момента просмотра."""

from starlette import status

from backend.application.dto.moment.delete_viewing_moment_command import (
    DeleteViewingMomentCommand,
)
from backend.application.interface.repositories.moment_repository import MomentRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult


class DeleteViewingMomentUseCase:
    """Удаляет черновик момента просмотра пользователя."""

    def __init__(self, uow: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий удаления момента просмотра.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
        """
        self._uow = uow

    async def execute(self, command: DeleteViewingMomentCommand) -> UseCaseResult:
        """Удаляет момент просмотра внутри транзакции.

        Args:
            command: Команда удаления черновика.

        Returns:
            UseCaseResult: Результат удаления.
        """
        async with self._uow as uow:
            deleted = await uow.repository(MomentRepository).delete_moment(
                command.moment_id, command.user_id
            )
        if not deleted:
            return UseCaseResult.failure("moment_not_found", status_code=status.HTTP_404_NOT_FOUND)
        return UseCaseResult.success({"deleted": True})
