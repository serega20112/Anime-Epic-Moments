from src.backend.domain.watch.entity import UserAnimeStatus
from src.backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from src.backend.repository.watch_repository import WatchRepository


class UpsertUserAnimeStatusUseCase:
    """Создает или обновляет статус просмотра аниме."""

    def __init__(
        self,
        watch_repo: WatchRepository,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.watch_repo = watch_repo
        self.profile_overview_cache = profile_overview_cache

    def execute(self, user_id: int, anime_id: int, status: str) -> UserAnimeStatus:
        result = self.watch_repo.upsert_status(
            UserAnimeStatus(user_id=user_id, anime_id=anime_id, status=status)
        )
        if self.profile_overview_cache is not None:
            self.profile_overview_cache.invalidate_overview(user_id)
        return result
