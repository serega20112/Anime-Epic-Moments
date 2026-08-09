from backend.application.dto import SetSavedHighlightCommand
from backend.application.use_cases.highlight.result import HighlightResult
from backend.domain.repositories.highlight_repository import HighlightRepository
from backend.domain.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)


class SetSavedHighlightUseCase:
    """Сохраняет или удаляет хайлайт из пользовательской коллекции."""

    def __init__(
            self,
            repo: HighlightRepository,
            profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.repo = repo
        self.profile_overview_cache = profile_overview_cache

    async def execute(self, command: SetSavedHighlightCommand) -> HighlightResult:
        """Save or unsave a highlight.

        Args:
            command: Set saved command.

        Returns:
            HighlightResult: Result with the saved state.
        """
        highlight = await self.repo.get_by_id(command.highlight_id)
        if not highlight:
            return HighlightResult.failure("highlight_not_found", status_code=404)
        result = await self.repo.set_saved(
            highlight_id=command.highlight_id,
            user_id=command.user_id,
            saved=command.saved,
        )
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_user(command.user_id)
        return HighlightResult.success(result)
