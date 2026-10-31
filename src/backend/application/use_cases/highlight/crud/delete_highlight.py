"""Удаление хайлайта владельцем."""

from __future__ import annotations

from starlette import status

from backend.application.dto import DeleteHighlightCommand
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.services import (
    HighlightDashboardCacheInterface,
    RecommendationServiceInterface,
)
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult


class DeleteHighlightUseCase:
    """Удаляет хайлайт только его автором в рамках транзакции."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationServiceInterface,
        highlight_dashboard_cache: HighlightDashboardCacheInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Инициализирует сценарий удаления хайлайта.

        Args:
            unit_of_work: Граница транзакции удаления хайлайта.
            recommendation_service: Сервис рекомендаций для сброса подборок.
            highlight_dashboard_cache: Кэш публичного дашборда хайлайтов.
            profile_overview_cache: Кэш обзора профиля автора.
        """
        self._unit_of_work = unit_of_work
        self._recommendation_service = recommendation_service
        self._highlight_dashboard_cache = highlight_dashboard_cache
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: DeleteHighlightCommand) -> UseCaseResult:
        """Удаляет хайлайт в рамках одной транзакции.

        Args:
            command: Команда удаления.

        Returns:
            UseCaseResult: Результат удаления либо код ошибки.
        """
        async with self._unit_of_work as uow:
            repository = uow.repository(HighlightRepository)
            highlight = await repository.get_by_id(command.highlight_id)
            if highlight is None:
                return UseCaseResult.failure(
                    "highlight_not_found", status_code=status.HTTP_404_NOT_FOUND
                )
            if not highlight.is_owned_by(command.user_id):
                return UseCaseResult.failure(
                    "highlight_forbidden", status_code=status.HTTP_403_FORBIDDEN
                )
            await repository.delete(command.highlight_id)
        await self._invalidate_caches(highlight.user_id)
        return UseCaseResult.success(status_code=status.HTTP_204_NO_CONTENT)

    async def _invalidate_caches(self, user_id: int | None) -> None:
        """Сбросить кэши, зависящие от удалённого хайлайта.

        Args:
            user_id: Идентификатор автора хайлайта.
        """
        await self._highlight_dashboard_cache.invalidate_public()
        if user_id is None:
            return
        await self._recommendation_service.invalidate_user(int(user_id))
        await self._profile_overview_cache.invalidate_user(int(user_id), include_ai_summary=True)
