from src.backend.domain.anime.value_object import AnimeDiscussionBoard
from src.backend.repository.watch_repository import WatchRepository


class GetAnimeDiscussionUseCase:
    """Собирает обсуждение аниме с сортировкой по популярности или свежести."""

    def __init__(self, watch_repo: WatchRepository):
        self.watch_repo = watch_repo

    def execute(
        self,
        anime_id: int,
        sort_by: str = "popular",
        viewer_user_id: int | None = None,
        limit: int = 20,
    ) -> AnimeDiscussionBoard:
        normalized_sort = str(sort_by or "popular").strip().lower()
        if normalized_sort not in {"popular", "recent"}:
            normalized_sort = "popular"
        items = self.watch_repo.get_anime_comments(
            anime_id=anime_id,
            sort_by=normalized_sort,
            viewer_user_id=viewer_user_id,
            limit=limit,
        )
        return AnimeDiscussionBoard(
            anime_id=anime_id,
            items=items,
            selected_sort=normalized_sort,
            total_comments=len(items),
        )
