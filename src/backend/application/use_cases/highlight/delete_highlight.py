from backend.application.dto import DeleteHighlightCommand
from backend.application.use_cases.highlight.result import HighlightResult
from backend.domain.repositories.highlight_repository import HighlightRepository
from backend.domain.services import (
    HighlightDashboardCacheInterface as HighlightDashboardCache,
)
from backend.domain.services import (
    RecommendationServiceInterface as RecommendationService,
)
from backend.domain.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.domain.unit_of_work import UnitOfWorkInterface


class DeleteHighlightUseCase:
    """Use case для удаления Highlight"""

    def __init__(
        self,
        repo: HighlightRepository,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationService | None = None,
        highlight_dashboard_cache: HighlightDashboardCache | None = None,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.repo = repo
        self.recommendation_service = recommendation_service
        self.highlight_dashboard_cache = highlight_dashboard_cache
        self.profile_overview_cache = profile_overview_cache
        self.unit_of_work = unit_of_work

    async def execute(self, command: DeleteHighlightCommand) -> HighlightResult:
        """Delete a highlight within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: DeleteHighlightCommand) -> HighlightResult:
        """Delete a highlight.

        Args:
            command: Delete highlight command.

        Returns:
            HighlightResult: Result of the deletion.
        """
        highlight = await self.repo.get_by_id(command.highlight_id)
        if not highlight:
            return await HighlightResult.failure("highlight_not_found", status_code=404)
        await self.repo.delete(command.highlight_id)
        if self.recommendation_service and highlight.user_id is not None:
            await self.recommendation_service.invalidate_user(int(highlight.user_id))
        if self.highlight_dashboard_cache is not None:
            await self.highlight_dashboard_cache.invalidate_public()
        if self.profile_overview_cache is not None and highlight.user_id is not None:
            await self.profile_overview_cache.invalidate_user(
                int(highlight.user_id),
                include_ai_summary=True,
            )
        return await HighlightResult.success(status_code=204)
