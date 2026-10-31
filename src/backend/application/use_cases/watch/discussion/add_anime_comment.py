"""Сценарий добавления комментария в обсуждение аниме."""

from __future__ import annotations

from starlette import status

from backend.application.dto import AddAnimeCommentCommand
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult

MIN_COMMENT_LENGTH = 2
MAX_COMMENT_LENGTH = 600


class AddAnimeCommentUseCase:
    """Добавляет комментарий в обсуждение аниме."""

    def __init__(self, unit_of_work: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий добавления комментария к аниме.

        Args:
            unit_of_work: Граница транзакции сохранения комментария.
        """
        self._unit_of_work = unit_of_work

    async def execute(self, command: AddAnimeCommentCommand) -> UseCaseResult:
        """Добавляет комментарий к аниме внутри транзакции.

        Args:
            command: Команда добавления комментария к аниме.

        Returns:
            UseCaseResult: Результат с созданным комментарием.
        """
        content = str(command.content or "").strip()
        if not MIN_COMMENT_LENGTH <= len(content) <= MAX_COMMENT_LENGTH:
            return UseCaseResult.failure(
                f"Комментарий должен быть от {MIN_COMMENT_LENGTH} до {MAX_COMMENT_LENGTH} символов",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        async with self._unit_of_work as uow:
            comment = await uow.repository(WatchRepository).add_anime_comment(
                anime_id=command.anime_id,
                user_id=command.user_id,
                content=content,
            )
        return UseCaseResult.success(comment, status_code=status.HTTP_201_CREATED)
