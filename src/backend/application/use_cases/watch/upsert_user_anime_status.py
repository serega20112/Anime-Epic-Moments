from backend.application.dto import UpsertUserAnimeStatusCommand
from backend.application.use_cases.watch.result import WatchResult
from backend.domain import UserAnimeStatus, WatchRepository
from backend.domain.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.domain.unit_of_work import UnitOfWorkInterface


class UpsertUserAnimeStatusUseCase:
    """Создает или обновляет статус просмотра аниме."""

    def __init__(
        self,
        watch_repo: WatchRepository,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.watch_repo = watch_repo
        self.profile_overview_cache = profile_overview_cache
        self.unit_of_work = unit_of_work

    async def execute(self, command: UpsertUserAnimeStatusCommand) -> WatchResult:
        """Upsert an anime status within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: UpsertUserAnimeStatusCommand) -> WatchResult:
        normalized_status = str(command.status or "").strip()
        if not normalized_status:
            return await WatchResult.failure("status_required", status_code=400)
        result = await self.watch_repo.upsert_status(
            UserAnimeStatus(
                user_id=command.user_id,
                anime_id=command.anime_id,
                status=normalized_status,
            )
        )
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_overview(command.user_id)
        return await WatchResult.success(result)
