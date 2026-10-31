"""Создание хайлайта по данным формы или плеера."""

from __future__ import annotations

from starlette import status

from backend.application.dto import CreateHighlightCommand
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
from backend.domain import Highlight, HighlightPolicy


class CreateHighlightUseCase:
    """Создаёт хайлайт пользователя в рамках транзакции."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationServiceInterface,
        highlight_dashboard_cache: HighlightDashboardCacheInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Инициализирует сценарий создания хайлайта.

        Args:
            unit_of_work: Граница транзакции сохранения хайлайта.
            recommendation_service: Сервис рекомендаций для сброса подборок.
            highlight_dashboard_cache: Кэш публичного дашборда хайлайтов.
            profile_overview_cache: Кэш обзора профиля автора.
        """
        self._unit_of_work = unit_of_work
        self._recommendation_service = recommendation_service
        self._highlight_dashboard_cache = highlight_dashboard_cache
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: CreateHighlightCommand) -> UseCaseResult:
        """Создаёт хайлайт внутри транзакции Unit of Work.

        Args:
            command: Команда создания хайлайта.

        Returns:
            UseCaseResult: Результат с созданным хайлайтом.
        """
        if not HighlightPolicy.can_add_highlight(command.user_id, command.highlights_this_hour):
            return UseCaseResult.failure(
                "Превышен лимит добавления хайлайтов для гостя",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        if not HighlightPolicy.is_content_allowed(f"{command.title} {command.description}"):
            return UseCaseResult.failure(
                "Описание содержит запрещённый контент",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        highlight = Highlight(
            user_id=command.user_id,
            anime_id=command.anime_id,
            episode=command.episode,
            start_timestamp=command.start_timestamp,
            end_timestamp=command.end_timestamp,
            title=command.title or f"Момент {command.episode} серии",
            category=command.category,
            description=command.description,
            is_spoiler=command.is_spoiler,
            emotion=command.emotion,
        )
        async with self._unit_of_work as uow:
            result = await uow.repository(HighlightRepository).add(highlight)
        await self._invalidate_caches(command.user_id)
        return UseCaseResult.success(result, status_code=status.HTTP_201_CREATED)

    async def _invalidate_caches(self, user_id: int | None) -> None:
        """Сбросить кэши, зависящие от нового хайлайта.

        Args:
            user_id: Идентификатор автора хайлайта либо None для гостя.
        """
        await self._highlight_dashboard_cache.invalidate_public()
        if user_id is None:
            return
        await self._recommendation_service.invalidate_user(int(user_id))
        await self._profile_overview_cache.invalidate_user(int(user_id), include_ai_summary=True)
