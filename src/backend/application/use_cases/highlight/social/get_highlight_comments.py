"""Сценарий чтения комментариев хайлайта."""

from __future__ import annotations

from backend.application.dto import HighlightCommentsQuery
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.highlight.social.limits import clamp_limit
from backend.domain import HighlightCommentItem


class GetHighlightCommentsUseCase:
    """Возвращает комментарии к хайлайту с ограничением по размеру выборки."""

    def __init__(self, unit_of_work: UnitOfWorkInterface) -> None:
        """Собрать сценарий чтения комментариев.

        Args:
            unit_of_work: Граница транзакции чтения комментариев.
        """
        self._unit_of_work = unit_of_work

    async def execute(self, query: HighlightCommentsQuery) -> list[HighlightCommentItem]:
        """Вернуть комментарии хайлайта с ограничением количества.

        Args:
            query: Идентификатор хайлайта и размер выборки.

        Returns:
            list[HighlightCommentItem]: Комментарии в порядке добавления.
        """
        async with self._unit_of_work as uow:
            return await uow.repository(HighlightRepository).get_comments(
                highlight_id=query.highlight_id,
                limit=clamp_limit(query.limit),
            )
