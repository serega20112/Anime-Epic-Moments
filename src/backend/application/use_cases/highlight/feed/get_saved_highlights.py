"""Сценарий дашборда сохранённых хайлайтов."""

from __future__ import annotations

from backend.application.dto import HighlightDashboardQuery
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.use_cases.highlight.feed.get_user_highlights import (
    GetUserHighlightsUseCase,
)
from backend.domain import Highlight


class GetSavedHighlightsUseCase(GetUserHighlightsUseCase):
    """Возвращает дашборд сохранённых пользователем хайлайтов."""

    async def _load(
        self,
        repository: HighlightRepository,
        query: HighlightDashboardQuery,
    ) -> list[Highlight]:
        """Загрузить хайлайты, сохранённые владельцем дашборда.

        Args:
            repository: Репозиторий хайлайтов текущей транзакции.
            query: Параметры дашборда с идентификатором владельца.

        Returns:
            list[Highlight]: Сохранённые хайлайты либо пустой список без владельца.
        """
        if query.user_id is None:
            return []
        return await repository.get_saved_by_user(query.user_id)
