from backend.application.dto import SetHighlightLikeCommand
from backend.application.use_cases.highlight.result import HighlightResult
from backend.domain.repositories.highlight_repository import HighlightRepository
from backend.domain.services import (
    HighlightDashboardCacheInterface as HighlightDashboardCache,
)
from backend.domain.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)


class SetHighlightLikeUseCase:
    """Ставит или снимает лайк с хайлайта."""

    def __init__(
            self,
            repo: HighlightRepository,
            highlight_dashboard_cache: HighlightDashboardCache | None = None,
            profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.repo = repo
        self.highlight_dashboard_cache = highlight_dashboard_cache
        self.profile_overview_cache = profile_overview_cache

    async def execute(self, command: SetHighlightLikeCommand) -> HighlightResult:
        """Set or remove a highlight like.

        Args:
            command: Set like command.

        Returns:
            HighlightResult: Result with the updated highlight.
        """
        highlight = await self.repo.get_by_id(command.highlight_id)
        if not highlight:
            return HighlightResult.failure("highlight_not_found", status_code=404)
        highlight = await self.repo.set_like(
            highlight_id=command.highlight_id,
            user_id=command.user_id,
            liked=command.liked,
        )
        if self.highlight_dashboard_cache is not None:
            await self.highlight_dashboard_cache.invalidate_public()
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_overview(command.user_id)
            if (
                    highlight.user_id is not None
                    and int(highlight.user_id) != int(command.user_id)
            ):
                await self.profile_overview_cache.invalidate_overview(
                    int(highlight.user_id)
                )
        return HighlightResult.success(highlight)
