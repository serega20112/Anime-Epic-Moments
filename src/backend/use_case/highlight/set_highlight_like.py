from src.backend.infrastructure.cache.highlight_dashboard_cache import (
    HighlightDashboardCache,
)
from src.backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from src.backend.repository.highlight_repository import HighlightRepository


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

    def execute(self, highlight_id: int, user_id: int, liked: bool):
        highlight = self.repo.set_like(highlight_id=highlight_id, user_id=user_id, liked=liked)
        if self.highlight_dashboard_cache is not None:
            self.highlight_dashboard_cache.invalidate_public()
        if self.profile_overview_cache is not None:
            self.profile_overview_cache.invalidate_overview(user_id)
            if highlight.user_id is not None and int(highlight.user_id) != int(user_id):
                self.profile_overview_cache.invalidate_overview(int(highlight.user_id))
        return highlight
