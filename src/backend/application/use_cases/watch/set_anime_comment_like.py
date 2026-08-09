from backend.application.dto import SetAnimeCommentLikeCommand
from backend.application.use_cases.watch.result import WatchResult
from backend.domain import WatchRepository


class SetAnimeCommentLikeUseCase:
    """Ставит или снимает лайк с комментария в обсуждении аниме."""

    def __init__(self, watch_repo: WatchRepository):
        self.watch_repo = watch_repo

    async def execute(self, command: SetAnimeCommentLikeCommand) -> WatchResult:
        try:
            comment = await self.watch_repo.set_anime_comment_like(
                comment_id=command.comment_id,
                user_id=command.user_id,
                liked=command.liked,
            )
        except ValueError:
            return WatchResult.failure("comment_not_found", status_code=404)
        return WatchResult.success(comment)
