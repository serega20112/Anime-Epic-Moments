from src.backend.domain.anime.value_object import AnimeDiscussionComment
from src.backend.repository.watch_repository import WatchRepository


class SetAnimeCommentLikeUseCase:
    """Ставит или снимает лайк с комментария в обсуждении аниме."""

    def __init__(self, watch_repo: WatchRepository):
        self.watch_repo = watch_repo

    async def execute(
        self,
        comment_id: int,
        user_id: int,
        liked: bool,
    ) -> AnimeDiscussionComment:
        return await self.watch_repo.set_anime_comment_like(
            comment_id=comment_id,
            user_id=user_id,
            liked=liked,
        )
