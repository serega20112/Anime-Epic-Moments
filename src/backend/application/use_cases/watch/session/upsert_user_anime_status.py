"""Сценарий сохранения статуса просмотра."""

from __future__ import annotations

from starlette import status

from backend.application.dto import UpsertUserAnimeStatusCommand
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult
from backend.domain import UserAnimeStatus


class UpsertUserAnimeStatusUseCase:
    """Создаёт или обновляет статус просмотра аниме."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Инициализирует сценарий upsert статуса просмотра аниме.

        Args:
            unit_of_work: Граница транзакции сохранения статуса.
            profile_overview_cache: Кэш обзора профиля пользователя.
        """
        self._unit_of_work = unit_of_work
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: UpsertUserAnimeStatusCommand) -> UseCaseResult:
        """Создаёт или обновляет статус просмотра аниме внутри транзакции.

        Args:
            command: Команда upsert статуса просмотра аниме.

        Returns:
            UseCaseResult: Результат операции upsert.
        """
        normalized_status = str(command.status or "").strip()
        if not normalized_status:
            return UseCaseResult.failure("status_required", status_code=status.HTTP_400_BAD_REQUEST)
        anime_status = UserAnimeStatus(
            user_id=command.user_id,
            anime_id=command.anime_id,
            status=normalized_status,
        )
        async with self._unit_of_work as uow:
            result = await uow.repository(WatchRepository).upsert_status(anime_status)
        await self._profile_overview_cache.invalidate_overview(command.user_id)
        return UseCaseResult.success(result)
