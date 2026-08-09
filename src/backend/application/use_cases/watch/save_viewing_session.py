from backend.application.dto import SaveViewingSessionCommand
from backend.application.use_cases.watch.result import WatchResult
from backend.domain import ViewingSession
from backend.domain import WatchRepository
from backend.domain.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)


class SaveViewingSessionUseCase:
    """Сохраняет текущую позицию просмотра пользователя."""

    def __init__(
            self,
            watch_repo: WatchRepository,
            profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.watch_repo = watch_repo
        self.profile_overview_cache = profile_overview_cache

    async def execute(self, command: SaveViewingSessionCommand) -> WatchResult:
        if command.episode is None or command.watch_source_id is None:
            return WatchResult.failure("invalid_payload", status_code=400)
        session = await self.watch_repo.upsert_session(
            ViewingSession(
                user_id=command.user_id,
                anime_id=command.anime_id,
                episode=command.episode,
                watch_source_id=command.watch_source_id,
                position_seconds=float(command.position_seconds or 0.0),
                volume=float(command.volume or 1.0),
                quality_label=str(command.quality_label or "Auto"),
                is_paused=bool(command.is_paused),
            )
        )
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_overview(command.user_id)
        return WatchResult.success(session)
