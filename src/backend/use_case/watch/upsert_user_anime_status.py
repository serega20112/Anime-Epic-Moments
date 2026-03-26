from src.backend.domain.watch.entity import UserAnimeStatus
from src.backend.repository.watch_repository import WatchRepository


class UpsertUserAnimeStatusUseCase:
    """Создает или обновляет статус просмотра аниме."""

    def __init__(self, watch_repo: WatchRepository):
        self.watch_repo = watch_repo

    def execute(self, user_id: int, anime_id: int, status: str) -> UserAnimeStatus:
        return self.watch_repo.upsert_status(
            UserAnimeStatus(user_id=user_id, anime_id=anime_id, status=status)
        )
