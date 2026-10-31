"""Сценарий постановки и снятия лайка хайлайту."""

from __future__ import annotations

from starlette import status

from backend.application.dto import SetHighlightLikeCommand
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.services import (
    HighlightDashboardCacheInterface,
)
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult


class SetHighlightLikeUseCase:
    """Ставит или снимает лайк с хайлайта в рамках транзакции."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        highlight_dashboard_cache: HighlightDashboardCacheInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Инициализирует сценарий установки лайка на хайлайт.

        Args:
            unit_of_work: Граница транзакции изменения лайка.
            highlight_dashboard_cache: Кэш публичного дашборда хайлайтов.
            profile_overview_cache: Кэш обзоров профиля зрителя и автора.
        """
        self._unit_of_work = unit_of_work
        self._highlight_dashboard_cache = highlight_dashboard_cache
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: SetHighlightLikeCommand) -> UseCaseResult:
        """Ставит или снимает лайк с хайлайта в рамках транзакции.

        Args:
            command: Команда установки или снятия лайка.

        Returns:
            UseCaseResult: Результат с обновлённым хайлайтом.
        """
        async with self._unit_of_work as uow:
            repository = uow.repository(HighlightRepository)
            if await repository.get_by_id(command.highlight_id) is None:
                return UseCaseResult.failure(
                    "highlight_not_found", status_code=status.HTTP_404_NOT_FOUND
                )
            highlight = await repository.set_like(
                highlight_id=command.highlight_id,
                user_id=command.user_id,
                liked=command.liked,
            )
        await self._highlight_dashboard_cache.invalidate_public()
        await self._profile_overview_cache.invalidate_overview(command.user_id)
        if highlight.user_id is not None and int(highlight.user_id) != int(command.user_id):
            await self._profile_overview_cache.invalidate_overview(int(highlight.user_id))
        return UseCaseResult.success(highlight)
