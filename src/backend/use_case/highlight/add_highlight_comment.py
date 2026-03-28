from src.backend.infrastructure.cache.highlight_dashboard_cache import (
    HighlightDashboardCache,
)
from src.backend.repository.highlight_repository import HighlightRepository


class AddHighlightCommentUseCase:
    """Добавляет комментарий к хайлайту после базовой валидации."""

    def __init__(
        self,
        repo: HighlightRepository,
        highlight_dashboard_cache: HighlightDashboardCache | None = None,
    ):
        self.repo = repo
        self.highlight_dashboard_cache = highlight_dashboard_cache

    def execute(self, highlight_id: int, user_id: int, content: str):
        normalized_content = str(content or "").strip()
        if not normalized_content:
            raise ValueError("Комментарий не может быть пустым")
        if len(normalized_content) > 600:
            raise ValueError("Комментарий слишком длинный")
        comment = self.repo.add_comment(
            highlight_id=highlight_id,
            user_id=user_id,
            content=normalized_content,
        )
        if self.highlight_dashboard_cache is not None:
            self.highlight_dashboard_cache.invalidate_public()
        return comment
