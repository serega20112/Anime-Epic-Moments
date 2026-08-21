from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.use_cases.watch.result import WatchResult
from backend.domain.value_objects.anime.discussion import AnimeDiscussionBoard


class GetAnimeDiscussionUseCase:
    """Собирает обсуждение аниме с сортировкой по популярности или свежести."""

    def __init__(self, watch_repo: WatchRepository):
        self.watch_repo = watch_repo

    async def execute(
        self,
        anime_id: int,
        sort_by: str = "popular",
        viewer_user_id: int | None = None,
        limit: int = 20,
    ) -> WatchResult:
        normalized_sort = str(sort_by or "popular").strip().lower()
        if normalized_sort not in {"popular", "recent"}:
            normalized_sort = "popular"
        try:
            items = await self.watch_repo.get_anime_comments(
                anime_id=anime_id,
                sort_by=normalized_sort,
                viewer_user_id=viewer_user_id,
                limit=limit,
            )
        except Exception:
            return await WatchResult.success(
                AnimeDiscussionBoard(
                    anime_id=anime_id,
                    items=[],
                    selected_sort=normalized_sort,
                    total_comments=0,
                )
            )
        return await WatchResult.success(
            AnimeDiscussionBoard(
                anime_id=anime_id,
                items=items,
                selected_sort=normalized_sort,
                total_comments=len(items),
            )
        )
