from starlette import status

from backend.application.dto import CreateHighlightCommand
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
from backend.domain import Highlight, HighlightPolicy


class CreateHighlightUseCase:
    """Use case для создания Highlight"""

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

    async def execute(self, command: CreateHighlightCommand) -> HighlightResult:
        """Create a highlight within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: CreateHighlightCommand) -> HighlightResult:
        """Create a highlight.

        Args:
            command: Create highlight command.

        Returns:
            HighlightResult: Result with the created highlight.
        """
        if not await HighlightPolicy.can_add_highlight(
            command.user_id, command.highlights_this_hour
        ):
            return await HighlightResult.failure(
                "Превышен лимит добавления хайлайтов для гостя",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if not await HighlightPolicy.filter_spoiler_content(
            f"{command.title} {command.description}"
        ):
            return await HighlightResult.failure(
                "Описание содержит запрещённый контент",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        highlight = Highlight(
            user_id=command.user_id,
            anime_id=command.anime_id,
            episode=command.episode,
            start_timestamp=command.start_timestamp,
            end_timestamp=command.end_timestamp,
            title=command.title or f"Момент {command.episode} серии",
            category=command.category,
            description=command.description,
            is_spoiler=command.is_spoiler,
            emotion=command.emotion,
        )

        result = await self.repo.add(highlight)
        if self.recommendation_service and command.user_id is not None:
            await self.recommendation_service.invalidate_user(int(command.user_id))
        if self.highlight_dashboard_cache is not None:
            await self.highlight_dashboard_cache.invalidate_public()
        if self.profile_overview_cache is not None and command.user_id is not None:
            await self.profile_overview_cache.invalidate_user(
                int(command.user_id),
                include_ai_summary=True,
            )
        return await HighlightResult.success(result, status_code=status.HTTP_201_CREATED)
