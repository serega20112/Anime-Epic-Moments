from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.services.recommendation_service import RecommendationService


class DeleteHighlightUseCase:
    """
    Use case для удаления Highlight
    """

    def __init__(
        self,
        repo: HighlightRepository,
        recommendation_service: RecommendationService | None = None,
    ):
        self.repo = repo
        self.recommendation_service = recommendation_service

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
