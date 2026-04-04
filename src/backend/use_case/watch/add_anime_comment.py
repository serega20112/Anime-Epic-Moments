from src.backend.domain.anime.value_object import AnimeDiscussionComment
from src.backend.repository.watch_repository import WatchRepository


class AddAnimeCommentUseCase:
    """Добавляет комментарий в обсуждение аниме."""

    def __init__(self, watch_repo: WatchRepository):
        self.watch_repo = watch_repo

    async def execute(self, anime_id: int, user_id: int, content: str) -> AnimeDiscussionComment:
        normalized_content = str(content or "").strip()
        if len(normalized_content) < 2 or len(normalized_content) > 600:
            raise ValueError("Комментарий должен быть от 2 до 600 символов")
        return await self.watch_repo.add_anime_comment(
            anime_id=anime_id,
            user_id=user_id,
            content=normalized_content,
        )
