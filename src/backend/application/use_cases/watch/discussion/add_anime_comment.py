from starlette import status

from backend.application.dto import AddAnimeCommentCommand
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.watch.result import WatchResult


class AddAnimeCommentUseCase:
    """Добавляет комментарий в обсуждение аниме."""

    def __init__(
        self,
        watch_repo: WatchRepository,
        unit_of_work: UnitOfWorkInterface,
    ):
        self.watch_repo = watch_repo
        self.unit_of_work = unit_of_work

    async def execute(self, command: AddAnimeCommentCommand) -> WatchResult:
        """Add an anime comment within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: AddAnimeCommentCommand) -> WatchResult:
        normalized_content = str(command.content or "").strip()
        if not normalized_content or len(normalized_content) < 2:
            return await WatchResult.failure(
                "Комментарий должен быть от 2 до 600 символов",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if len(normalized_content) > 600:
            return await WatchResult.failure(
                "Комментарий должен быть от 2 до 600 символов",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        comment = await self.watch_repo.add_anime_comment(
            anime_id=command.anime_id,
            user_id=command.user_id,
            content=normalized_content,
        )
        return await WatchResult.success(comment, status_code=status.HTTP_201_CREATED)
