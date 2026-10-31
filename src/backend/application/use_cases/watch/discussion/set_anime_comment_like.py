"""Сценарий лайка комментария в обсуждении."""

from __future__ import annotations

from starlette import status

from backend.application.dto import SetAnimeCommentLikeCommand
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult


class SetAnimeCommentLikeUseCase:
    """Ставит или снимает лайк с комментария в обсуждении аниме."""

    def __init__(self, unit_of_work: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий установки лайка на комментарий аниме.

        Args:
            unit_of_work: Граница транзакции изменения лайка.
        """
        self._unit_of_work = unit_of_work

    async def execute(self, command: SetAnimeCommentLikeCommand) -> UseCaseResult:
        """Ставит или снимает лайк с комментария аниме внутри транзакции.

        Args:
            command: Команда установки или снятия лайка с комментария.

        Returns:
            UseCaseResult: Результат операции с комментарием.
        """
        async with self._unit_of_work as uow:
            try:
                comment = await uow.repository(WatchRepository).set_anime_comment_like(
                    comment_id=command.comment_id,
                    user_id=command.user_id,
                    liked=command.liked,
                )
            except ValueError:
                return UseCaseResult.failure(
                    "comment_not_found", status_code=status.HTTP_404_NOT_FOUND
                )
        return UseCaseResult.success(comment)
