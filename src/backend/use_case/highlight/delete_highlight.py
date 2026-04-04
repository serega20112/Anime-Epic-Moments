from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.infrastructure.cache.highlight_dashboard_cache import (
    HighlightDashboardCache,
)
from src.backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from src.backend.services.recommendation_service import RecommendationService


class DeleteHighlightUseCase:
    """
    Use case для удаления Highlight
    """

    def __init__(
        self,
        repo: HighlightRepository,
        recommendation_service: RecommendationService | None = None,
        highlight_dashboard_cache: HighlightDashboardCache | None = None,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.repo = repo
        self.recommendation_service = recommendation_service
        self.highlight_dashboard_cache = highlight_dashboard_cache
        self.profile_overview_cache = profile_overview_cache

    def execute(self, highlight_id: int):
        """
        Удаляет хайлайт по ID
        """
        highlight = self.repo.get_by_id(highlight_id)
        if not highlight:
            raise ValueError("Highlight не найден")
        self.repo.delete(highlight_id)
        if self.recommendation_service and highlight.user_id is not None:
            self.recommendation_service.invalidate_user(int(highlight.user_id))
        if self.highlight_dashboard_cache is not None:
            self.highlight_dashboard_cache.invalidate_public()
        if self.profile_overview_cache is not None and highlight.user_id is not None:
            self.profile_overview_cache.invalidate_user(
                int(highlight.user_id),
                include_ai_summary=True,
            )
