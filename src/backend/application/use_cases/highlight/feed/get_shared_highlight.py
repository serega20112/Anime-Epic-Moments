"""Сценарий публичной карточки одного хайлайта."""

from __future__ import annotations

from starlette import status

from backend.application.dto import HighlightDashboardQuery, HighlightSharedQuery
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.use_cases.highlight.feed.get_user_highlights import (
    GetUserHighlightsUseCase,
)
from backend.application.use_cases.result import UseCaseResult


class GetSharedHighlightUseCase(GetUserHighlightsUseCase):
    """Возвращает публичную карточку одного хайлайта и увеличивает счётчик просмотров."""

    async def execute(self, query: HighlightSharedQuery) -> UseCaseResult:
        """Возвращает общий хайлайт внутри транзакции.

        Args:
            query: Идентификатор хайлайта и зритель для отметок лайков.

        Returns:
            UseCaseResult: Результат с карточкой хайлайта.
        """
        async with self._unit_of_work as uow:
            repository = uow.repository(HighlightRepository)
            highlight = await repository.get_by_id(query.highlight_id)
            if highlight is None:
                return UseCaseResult.failure(
                    "highlight_not_found", status_code=status.HTTP_404_NOT_FOUND
                )
            await repository.increment_views(query.highlight_id)
            engagement_map = await repository.get_engagement_map(
                [query.highlight_id],
                viewer_user_id=query.viewer_user_id,
            )
            owner_map = await self._load_owners(uow, [highlight])
        dashboard = await self._build_dashboard(
            [highlight],
            HighlightDashboardQuery(include_spoilers=True, viewer_user_id=query.viewer_user_id),
            engagement_map,
            owner_map,
        )
        return UseCaseResult.success(dashboard)
