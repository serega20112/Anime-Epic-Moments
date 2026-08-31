from starlette import status

from backend.application.dto import CompleteEpisodeCommand
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.watch.result import WatchResult


class CompleteEpisodeUseCase:
    """Записывает событие «досмотрено» после просмотра эпизода."""

    def __init__(
        self,
        watch_repo: WatchRepository,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.watch_repo = watch_repo
        self.unit_of_work = unit_of_work
        self.profile_overview_cache = profile_overview_cache

    async def execute(self, command: CompleteEpisodeCommand) -> WatchResult:
        """Record a completed episode within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: CompleteEpisodeCommand) -> WatchResult:
        if command.episode is None or command.episode < 1:
            return await WatchResult.failure(
                "invalid_episode", status_code=status.HTTP_400_BAD_REQUEST
            )
        result = await self.watch_repo.record_episode_completion(
            user_id=command.user_id,
            anime_id=command.anime_id,
            episode=command.episode,
        )
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_overview(command.user_id)
        return await WatchResult.success(result)
