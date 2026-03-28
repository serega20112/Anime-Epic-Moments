from src.backend.infrastructure.cache.highlight_dashboard_cache import (
    HighlightDashboardCache,
)
from src.backend.repository.highlight_repository import HighlightRepository


class SetHighlightLikeUseCase:
    """Ставит или снимает лайк с хайлайта."""

    def __init__(
        self,
        repo: HighlightRepository,
        highlight_dashboard_cache: HighlightDashboardCache | None = None,
    ):
        self.repo = repo
        self.highlight_dashboard_cache = highlight_dashboard_cache

    def execute(self, highlight_id: int, user_id: int, liked: bool):
        highlight = self.repo.set_like(highlight_id=highlight_id, user_id=user_id, liked=liked)
        if self.highlight_dashboard_cache is not None:
            self.highlight_dashboard_cache.invalidate_public()
        return highlight
