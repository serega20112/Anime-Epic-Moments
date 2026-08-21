from starlette import status

from backend.application.dto import AddHighlightCommentCommand
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.services import (
    HighlightDashboardCacheInterface as HighlightDashboardCache,
)
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.highlight.result import HighlightResult


class AddHighlightCommentUseCase:
    """Добавляет комментарий к хайлайту после базовой валидации."""

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

    async def execute(self, command: AddHighlightCommentCommand) -> HighlightResult:
        """Add a highlight comment within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: AddHighlightCommentCommand) -> HighlightResult:
        """Add a comment to a highlight.

        Args:
            command: Add comment command.

        Returns:
            HighlightResult: Result with the created comment.
        """
        normalized_content = str(command.content or "").strip()
        if not normalized_content:
            return await HighlightResult.failure(
                "Комментарий не может быть пустым", status_code=status.HTTP_400_BAD_REQUEST
            )
        if len(normalized_content) > 600:
            return await HighlightResult.failure(
                "Комментарий слишком длинный", status_code=status.HTTP_400_BAD_REQUEST
            )
        highlight = await self.repo.get_by_id(command.highlight_id)
        if not highlight:
            return await HighlightResult.failure(
                "highlight_not_found", status_code=status.HTTP_404_NOT_FOUND
            )
        comment = await self.repo.add_comment(
            highlight_id=command.highlight_id,
            user_id=command.user_id,
            content=normalized_content,
        )
        if self.highlight_dashboard_cache is not None:
            await self.highlight_dashboard_cache.invalidate_public()
        if self.profile_overview_cache is not None and highlight.user_id is not None:
            await self.profile_overview_cache.invalidate_user(highlight.user_id)
        return await HighlightResult.success(comment, status_code=status.HTTP_201_CREATED)
