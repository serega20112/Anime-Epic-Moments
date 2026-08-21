from starlette import status

from backend.application.dto import SaveViewingSessionCommand
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.watch.result import WatchResult
from backend.domain import ViewingSession


class SaveViewingSessionUseCase:
    """Сохраняет текущую позицию просмотра пользователя."""

    def __init__(
        self,
        watch_repo: WatchRepository,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.watch_repo = watch_repo
        self.profile_overview_cache = profile_overview_cache
        self.unit_of_work = unit_of_work

    async def execute(self, command: SaveViewingSessionCommand) -> WatchResult:
        """Save a viewing session within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: SaveViewingSessionCommand) -> WatchResult:
        if command.episode is None or command.watch_source_id is None:
            return await WatchResult.failure(
                "invalid_payload", status_code=status.HTTP_400_BAD_REQUEST
            )
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
        return await WatchResult.success(session)
