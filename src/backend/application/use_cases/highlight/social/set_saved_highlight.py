"""Сценарий сохранения и удаления хайлайта из сохранённых."""

from __future__ import annotations

from starlette import status

from backend.application.dto import SetSavedHighlightCommand
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult


class SetSavedHighlightUseCase:
    """Сохраняет или удаляет хайлайт из пользовательской коллекции."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Инициализирует сценарий сохранения хайлайта.

        Args:
            unit_of_work: Граница транзакции изменения отметки сохранения.
            profile_overview_cache: Кэш обзора профиля зрителя.
        """
        self._unit_of_work = unit_of_work
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: SetSavedHighlightCommand) -> UseCaseResult:
        """Сохраняет или удаляет хайлайт из коллекции внутри транзакции.

        Args:
            command: Команда сохранения или удаления из коллекции.

        Returns:
            UseCaseResult: Результат с состоянием сохранения.
        """
        async with self._unit_of_work as uow:
            repository = uow.repository(HighlightRepository)
            if await repository.get_by_id(command.highlight_id) is None:
                return UseCaseResult.failure(
                    "highlight_not_found", status_code=status.HTTP_404_NOT_FOUND
                )
            saved = await repository.set_saved(
                highlight_id=command.highlight_id,
                user_id=command.user_id,
                saved=command.saved,
            )
        await self._profile_overview_cache.invalidate_user(command.user_id)
        return UseCaseResult.success(saved)
