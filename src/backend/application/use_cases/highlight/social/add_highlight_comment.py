"""Сценарий добавления комментария к хайлайту."""

from __future__ import annotations

from starlette import status

from backend.application.dto import AddHighlightCommentCommand
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.services import (
    HighlightDashboardCacheInterface,
)
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult

MAX_COMMENT_LENGTH = 600


class AddHighlightCommentUseCase:
    """Добавляет комментарий к хайлайту после базовой валидации."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        highlight_dashboard_cache: HighlightDashboardCacheInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Инициализирует сценарий добавления комментария к хайлайту.

        Args:
            unit_of_work: Граница транзакции сохранения комментария.
            highlight_dashboard_cache: Кэш публичного дашборда хайлайтов.
            profile_overview_cache: Кэш обзора профиля автора хайлайта.
        """
        self._unit_of_work = unit_of_work
        self._highlight_dashboard_cache = highlight_dashboard_cache
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: AddHighlightCommentCommand) -> UseCaseResult:
        """Добавляет комментарий к хайлайту внутри транзакции.

        Args:
            command: Команда добавления комментария.

        Returns:
            UseCaseResult: Результат с созданным комментарием.
        """
        content = str(command.content or "").strip()
        if not content:
            return UseCaseResult.failure(
                "Комментарий не может быть пустым", status_code=status.HTTP_400_BAD_REQUEST
            )
        if len(content) > MAX_COMMENT_LENGTH:
            return UseCaseResult.failure(
                "Комментарий слишком длинный", status_code=status.HTTP_400_BAD_REQUEST
            )

        async with self._unit_of_work as uow:
            repository = uow.repository(HighlightRepository)
            highlight = await repository.get_by_id(command.highlight_id)
            if highlight is None:
                return UseCaseResult.failure(
                    "highlight_not_found", status_code=status.HTTP_404_NOT_FOUND
                )
            comment = await repository.add_comment(
                highlight_id=command.highlight_id,
                user_id=command.user_id,
                content=content,
            )
        await self._highlight_dashboard_cache.invalidate_public()
        if highlight.user_id is not None:
            await self._profile_overview_cache.invalidate_user(int(highlight.user_id))
        return UseCaseResult.success(comment, status_code=status.HTTP_201_CREATED)
