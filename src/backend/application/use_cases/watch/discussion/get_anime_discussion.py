"""Обсуждение аниме на странице просмотра."""

from __future__ import annotations

import logging

from backend.application.dto import AnimeDiscussionQuery
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult
from backend.domain.value_objects.anime.discussion import AnimeDiscussionBoard

logger = logging.getLogger("anime_epic_moments")

ALLOWED_SORTS = {"popular", "recent"}


class GetAnimeDiscussionUseCase:
    """Собирает обсуждение аниме с сортировкой по популярности или свежести."""

    def __init__(self, unit_of_work: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий получения обсуждения аниме.

        Args:
            unit_of_work: Граница транзакции чтения комментариев.
        """
        self._unit_of_work = unit_of_work

    async def execute(self, query: AnimeDiscussionQuery) -> UseCaseResult:
        """Возвращает обсуждение аниме; при сбое чтения — пустую доску.

        Захват широкий намеренно: отсутствие комментариев из-за сбоя базы не
        должно ломать страницу просмотра, где обсуждение второстепенно. Случай
        не проглатывается: он уходит в лог уровнем ERROR со stack trace, чтобы
        настоящий баг кода отличался от штатного сбоя базы.

        Args:
            query: Идентификатор аниме, сортировка, зритель и размер выборки.

        Returns:
            UseCaseResult: Карточка обсуждения.
        """
        sort_by = self._normalize_sort(query.sort_by)
        try:
            async with self._unit_of_work as uow:
                items = await uow.repository(WatchRepository).get_anime_comments(
                    anime_id=query.anime_id,
                    sort_by=sort_by,
                    viewer_user_id=query.viewer_user_id,
                    limit=query.limit,
                )
        except Exception:
            logger.exception("anime_discussion_read_failed anime_id=%s", query.anime_id)
            items = []
        return UseCaseResult.success(
            AnimeDiscussionBoard(
                anime_id=query.anime_id,
                items=items,
                selected_sort=sort_by,
                total_comments=len(items),
            )
        )

    @staticmethod
    def _normalize_sort(sort_by: str) -> str:
        """Привести критерий сортировки к допустимому набору.

        Args:
            sort_by: Исходный критерий сортировки.

        Returns:
            str: 'popular' или 'recent'; при неизвестном значении — 'popular'.
        """
        normalized = str(sort_by or "popular").strip().lower()
        return normalized if normalized in ALLOWED_SORTS else "popular"
