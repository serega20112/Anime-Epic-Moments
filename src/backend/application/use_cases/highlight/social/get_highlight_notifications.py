"""Сценарий уведомлений о действиях с хайлайтами."""

from __future__ import annotations

from backend.application.dto import HighlightNotificationsQuery
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.highlight.social.limits import clamp_limit
from backend.domain import HighlightActivityItem


class GetHighlightNotificationsUseCase:
    """Возвращает простые уведомления по реакциям на хайлайты пользователя."""

    def __init__(self, unit_of_work: UnitOfWorkInterface) -> None:
        """Собрать сценарий уведомлений.

        Args:
            unit_of_work: Граница транзакции чтения активности.
        """
        self._unit_of_work = unit_of_work

    async def execute(self, query: HighlightNotificationsQuery) -> list[HighlightActivityItem]:
        """Вернуть недавнюю активность по хайлайтам пользователя.

        Args:
            query: Идентификатор владельца хайлайтов и размер выборки.

        Returns:
            list[HighlightActivityItem]: Последние реакции сообщества.
        """
        async with self._unit_of_work as uow:
            return await uow.repository(HighlightRepository).get_recent_activity(
                user_id=query.user_id,
                limit=clamp_limit(query.limit),
            )
