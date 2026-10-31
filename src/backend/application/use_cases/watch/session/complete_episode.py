"""Сценарий отметки просмотренной серии."""

from __future__ import annotations

from starlette import status

from backend.application.dto import CompleteEpisodeCommand
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult


class CompleteEpisodeUseCase:
    """Записывает событие «досмотрено» после просмотра эпизода."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Инициализирует сценарий завершения эпизода.

        Args:
            unit_of_work: Граница транзакции записи завершения.
            profile_overview_cache: Кэш обзора профиля пользователя.
        """
        self._unit_of_work = unit_of_work
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: CompleteEpisodeCommand) -> UseCaseResult:
        """Записывает событие завершения эпизода внутри транзакции.

        Args:
            command: Команда завершения эпизода.

        Returns:
            UseCaseResult: Результат записи завершения эпизода.
        """
        if command.episode is None or command.episode < 1:
            return UseCaseResult.failure("invalid_episode", status_code=status.HTTP_400_BAD_REQUEST)
        async with self._unit_of_work as uow:
            result = await uow.repository(WatchRepository).record_episode_completion(
                user_id=command.user_id,
                anime_id=command.anime_id,
                episode=command.episode,
            )
        await self._profile_overview_cache.invalidate_overview(command.user_id)
        return UseCaseResult.success(result)
