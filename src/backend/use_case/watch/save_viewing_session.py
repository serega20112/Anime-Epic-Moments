from src.backend.domain.watch.entity import ViewingSession
from src.backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from src.backend.repository.watch_repository import WatchRepository


class SaveViewingSessionUseCase:
    """Сохраняет текущую позицию просмотра пользователя."""

    def __init__(
        self,
        watch_repo: WatchRepository,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.watch_repo = watch_repo
        self.profile_overview_cache = profile_overview_cache

    def execute(
        self,
        user_id: int,
        anime_id: int,
        episode: int,
        watch_source_id: int,
        position_seconds: float,
        volume: float,
        quality_label: str,
        is_paused: bool,
    ) -> ViewingSession:
        session = self.watch_repo.upsert_session(
            ViewingSession(
                user_id=user_id,
                anime_id=anime_id,
                episode=episode,
                watch_source_id=watch_source_id,
                position_seconds=position_seconds,
                volume=volume,
                quality_label=quality_label,
                is_paused=is_paused,
            )
        )
        if self.profile_overview_cache is not None:
            self.profile_overview_cache.invalidate_overview(user_id)
        return session
