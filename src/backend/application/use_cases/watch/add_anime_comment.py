from backend.application.dto import AddAnimeCommentCommand
from backend.application.use_cases.watch.result import WatchResult
from backend.domain import WatchRepository


class AddAnimeCommentUseCase:
    """Добавляет комментарий в обсуждение аниме."""

    def __init__(self, watch_repo: WatchRepository):
        self.watch_repo = watch_repo

    async def execute(self, command: AddAnimeCommentCommand) -> WatchResult:
        normalized_content = str(command.content or "").strip()
        if not normalized_content or len(normalized_content) < 2:
            return WatchResult.failure(
                "Комментарий должен быть от 2 до 600 символов",
                status_code=400,
            )
        if len(normalized_content) > 600:
            return WatchResult.failure(
                "Комментарий должен быть от 2 до 600 символов",
                status_code=400,
            )
        comment = await self.watch_repo.add_anime_comment(
            anime_id=command.anime_id,
            user_id=command.user_id,
            content=normalized_content,
        )
        return WatchResult.success(comment, status_code=201)
