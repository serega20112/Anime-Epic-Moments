"""Правка хайлайта владельцем."""

from __future__ import annotations

from starlette import status

from backend.application.dto import EditHighlightCommand
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
from backend.domain import HighlightPolicy
from backend.domain.exceptions import ValidationError


class EditHighlightUseCase:
    """Редактирует хайлайт только его автором в рамках транзакции."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationServiceInterface,
        highlight_dashboard_cache: HighlightDashboardCacheInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Инициализирует сценарий редактирования хайлайта.

        Args:
            unit_of_work: Граница транзакции правки хайлайта.
            recommendation_service: Сервис рекомендаций для сброса подборок.
            highlight_dashboard_cache: Кэш публичного дашборда хайлайтов.
            profile_overview_cache: Кэш обзора профиля автора.
        """
        self._unit_of_work = unit_of_work
        self._recommendation_service = recommendation_service
        self._highlight_dashboard_cache = highlight_dashboard_cache
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: EditHighlightCommand) -> UseCaseResult:
        """Редактирует хайлайт в рамках одной транзакции.

        Args:
            command: Команда редактирования.

        Returns:
            UseCaseResult: Обновлённый хайлайт либо код ошибки.
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
            if not HighlightPolicy.is_content_allowed(f"{command.title} {command.description}"):
                return UseCaseResult.failure(
                    "Описание содержит запрещённый контент",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            try:
                highlight.edit(
                    start_timestamp=command.start_timestamp,
                    end_timestamp=command.end_timestamp,
                    title=command.title or highlight.title or f"Момент {highlight.episode} серии",
                    category=command.category,
                    description=command.description,
                    is_spoiler=command.is_spoiler,
                    emotion=command.emotion,
                    episode=command.episode,
                )
            except ValidationError as error:
                return UseCaseResult.failure(str(error), status_code=status.HTTP_400_BAD_REQUEST)
            result = await repository.update(highlight)
        await self._invalidate_caches(highlight.user_id)
        return UseCaseResult.success(result)

    async def _invalidate_caches(self, user_id: int | None) -> None:
        """Сбросить кэши, зависящие от изменённого хайлайта.

        Args:
            user_id: Идентификатор автора хайлайта.
        """
        await self._highlight_dashboard_cache.invalidate_public()
        if user_id is None:
            return
        await self._recommendation_service.invalidate_user(int(user_id))
        await self._profile_overview_cache.invalidate_user(int(user_id), include_ai_summary=True)
