from backend.application.dto import SetSavedHighlightCommand
from backend.application.use_cases.highlight.result import HighlightResult
from backend.domain.repositories.highlight_repository import HighlightRepository
from backend.domain.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.domain.unit_of_work import UnitOfWorkInterface


class SetSavedHighlightUseCase:
    """Сохраняет или удаляет хайлайт из пользовательской коллекции."""

    def __init__(
            self,
            repo: HighlightRepository,
            profile_overview_cache: ProfileOverviewCache | None = None,
            unit_of_work: UnitOfWorkInterface | None = None,
    ):
        self.repo = repo
        self.profile_overview_cache = profile_overview_cache
        self.unit_of_work = unit_of_work

    async def execute(self, command: SetSavedHighlightCommand) -> HighlightResult:
        """Save or unsave a highlight within a transaction if configured."""
        if self.unit_of_work is None:
            return await self._execute(command)
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: SetSavedHighlightCommand) -> HighlightResult:
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
