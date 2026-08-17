from backend.application.dto import SetAnimeCommentLikeCommand
from backend.application.use_cases.watch.result import WatchResult
from backend.domain import WatchRepository
from backend.domain.unit_of_work import UnitOfWorkInterface


class SetAnimeCommentLikeUseCase:
    """Ставит или снимает лайк с комментария в обсуждении аниме."""

    def __init__(
        self,
        watch_repo: WatchRepository,
        unit_of_work: UnitOfWorkInterface,
    ):
        self.watch_repo = watch_repo
        self.unit_of_work = unit_of_work

    async def execute(self, command: SetAnimeCommentLikeCommand) -> WatchResult:
        """Set an anime comment like within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: SetAnimeCommentLikeCommand) -> WatchResult:
        try:
            comment = await self.watch_repo.set_anime_comment_like(
                comment_id=command.comment_id,
                user_id=command.user_id,
                liked=command.liked,
            )
        except ValueError:
            return await WatchResult.failure("comment_not_found", status_code=404)
        return await WatchResult.success(comment)
