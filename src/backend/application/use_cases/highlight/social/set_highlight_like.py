from starlette import status

from backend.application.dto import SetHighlightLikeCommand
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.services import (
    HighlightDashboardCacheInterface as HighlightDashboardCache,
)
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.highlight.result import HighlightResult


class SetHighlightLikeUseCase:
    """Ставит или снимает лайк с хайлайта."""

    def __init__(
        self,
        repo: HighlightRepository,
        unit_of_work: UnitOfWorkInterface,
        highlight_dashboard_cache: HighlightDashboardCache | None = None,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.repo = repo
        self.highlight_dashboard_cache = highlight_dashboard_cache
        self.profile_overview_cache = profile_overview_cache
        self.unit_of_work = unit_of_work

    async def execute(self, command: SetHighlightLikeCommand) -> HighlightResult:
        """Set a highlight like within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: SetHighlightLikeCommand) -> HighlightResult:
        """Set or remove a highlight like.

        Args:
            command: Set like command.

        Returns:
            HighlightResult: Result with the updated highlight.
        """
        highlight = await self.repo.get_by_id(command.highlight_id)
        if not highlight:
            return await HighlightResult.failure(
                "highlight_not_found", status_code=status.HTTP_404_NOT_FOUND
            )
        highlight = await self.repo.set_like(
            highlight_id=command.highlight_id,
            user_id=command.user_id,
            liked=command.liked,
        )
        if self.highlight_dashboard_cache is not None:
            await self.highlight_dashboard_cache.invalidate_public()
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_overview(command.user_id)
            if highlight.user_id is not None and int(highlight.user_id) != int(command.user_id):
                await self.profile_overview_cache.invalidate_overview(int(highlight.user_id))
        return await HighlightResult.success(highlight)
