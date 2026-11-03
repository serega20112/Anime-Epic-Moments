"""Сценарий постановки и снятия лайка хайлайту."""

from __future__ import annotations

from starlette import status

from backend.application.dto import SetHighlightLikeCommand
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.repositories.notification_repository import (
    NotificationRepository,
)
from backend.application.interface.services import (
    HighlightDashboardCacheInterface,
)
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult
from backend.domain import Notification
from backend.domain.entities.notification.notification import KIND_HIGHLIGHT_LIKE
from backend.domain.policies.notification_policy import notification_text


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
            await self._notify_owner(uow, command, highlight)
        await self._highlight_dashboard_cache.invalidate_public()
        await self._profile_overview_cache.invalidate_overview(command.user_id)
        if highlight.user_id is not None and int(highlight.user_id) != int(command.user_id):
            await self._profile_overview_cache.invalidate_overview(int(highlight.user_id))
        return UseCaseResult.success(highlight)

    @staticmethod
    async def _notify_owner(uow: UnitOfWorkInterface, command, highlight) -> None:
        """Записать владельцу хайлайта уведомление о лайке, если это не его лайк.

        Снятие лайка уведомления не создаёт, и собственное действие автора не
        анонсируется ему же.

        Args:
            uow: Граница транзакции с доступом к репозиторию уведомлений.
            command: Команда установки лайка.
            highlight: Обновлённый хайлайт с идентификатором владельца.
        """
        if not command.liked:
            return
        if highlight.user_id is None or int(highlight.user_id) == int(command.user_id):
            return
        await uow.repository(NotificationRepository).add(
            Notification(
                user_id=int(highlight.user_id),
                kind=KIND_HIGHLIGHT_LIKE,
                text=notification_text(KIND_HIGHLIGHT_LIKE),
                actor_user_id=command.user_id,
                anime_id=highlight.anime_id,
                highlight_id=highlight.id,
            )
        )
