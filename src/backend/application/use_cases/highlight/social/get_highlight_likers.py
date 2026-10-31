"""Сценарий чтения пользователей, поставивших лайк."""

from __future__ import annotations

from backend.application.dto import HighlightLikersQuery
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.highlight.social.limits import clamp_limit
from backend.domain import HighlightLikeUser


class GetHighlightLikersUseCase:
    """Возвращает пользователей, поставивших лайк хайлайту."""

    def __init__(self, unit_of_work: UnitOfWorkInterface) -> None:
        """Собрать сценарий чтения лайкнувших.

        Args:
            unit_of_work: Граница транзакции чтения лайков.
        """
        self._unit_of_work = unit_of_work

    async def execute(self, query: HighlightLikersQuery) -> list[HighlightLikeUser]:
        """Вернуть пользователей, поставивших лайк хайлайту.

        Args:
            query: Идентификатор хайлайта и размер выборки.

        Returns:
            list[HighlightLikeUser]: Пользователи в порядке последних лайков.
        """
        async with self._unit_of_work as uow:
            return await uow.repository(HighlightRepository).get_likers(
                highlight_id=query.highlight_id,
                limit=clamp_limit(query.limit),
            )
