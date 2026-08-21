from starlette import status

from backend.application.dto import EditHighlightCommand
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.services import (
    HighlightDashboardCacheInterface as HighlightDashboardCache,
)
from backend.application.interface.services import (
    RecommendationServiceInterface as RecommendationService,
)
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.highlight.result import HighlightResult
from backend.domain import HighlightPolicy


class EditHighlightUseCase:
    """Use case для редактирования Highlight"""

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

    async def execute(self, command: EditHighlightCommand) -> HighlightResult:
        """Edit a highlight within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: EditHighlightCommand) -> HighlightResult:
        """Edit a highlight.

        Args:
            command: Edit highlight command.

        Returns:
            HighlightResult: Result with the updated highlight.
        """
        highlight = await self.repo.get_by_id(command.highlight_id)
        if not highlight:
            return await HighlightResult.failure(
                "highlight_not_found", status_code=status.HTTP_404_NOT_FOUND
            )

        if not HighlightPolicy.filter_spoiler_content(f"{command.title} {command.description}"):
            return await HighlightResult.failure(
                "Описание содержит запрещённый контент",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        highlight.edit(
            start_timestamp=command.start_timestamp,
            end_timestamp=command.end_timestamp,
            title=command.title or highlight.title or f"Момент {highlight.episode} серии",
            category=command.category,
            description=command.description,
            is_spoiler=command.is_spoiler,
            emotion=command.emotion,
        )
        if command.episode is not None:
            highlight.episode = int(command.episode)

        result = await self.repo.update(highlight)
        if self.recommendation_service and highlight.user_id is not None:
            await self.recommendation_service.invalidate_user(int(highlight.user_id))
        if self.highlight_dashboard_cache is not None:
            await self.highlight_dashboard_cache.invalidate_public()
        if self.profile_overview_cache is not None and highlight.user_id is not None:
            await self.profile_overview_cache.invalidate_user(
                int(highlight.user_id),
                include_ai_summary=True,
            )
        return await HighlightResult.success(result, status_code=status.HTTP_204_NO_CONTENT)
