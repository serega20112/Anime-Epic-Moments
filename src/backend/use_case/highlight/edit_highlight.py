from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.domain.highlight.entity import Highlight
from src.backend.domain.highlight.policy import HighlightPolicy
from src.backend.infrastructure.cache.highlight_dashboard_cache import (
    HighlightDashboardCache,
)
from src.backend.services.recommendation_service import RecommendationService


class EditHighlightUseCase:
    """
    Use case для редактирования Highlight
    """

    def __init__(
        self,
        repo: HighlightRepository,
        recommendation_service: RecommendationService | None = None,
        highlight_dashboard_cache: HighlightDashboardCache | None = None,
    ):
        self.repo = repo
        self.recommendation_service = recommendation_service
        self.highlight_dashboard_cache = highlight_dashboard_cache

    def execute(
        self,
        highlight_id: int,
        episode: int | None,
        start_timestamp: float,
        end_timestamp: float,
        description: str,
        is_spoiler: bool,
        emotion: str | None = None,
    ) -> Highlight:
        """
        Редактирует существующий хайлайт.
        Проверяет инварианты времени и запрещённый контент.
        """
        highlight = self.repo.get_by_id(highlight_id)
        if not highlight:
            raise ValueError("Highlight не найден")

        if not HighlightPolicy.filter_spoiler_content(description):
            raise ValueError("Описание содержит запрещённый контент")

        highlight.edit(
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            description=description,
            is_spoiler=is_spoiler,
        )
        if episode is not None:
            highlight.episode = int(episode)
        highlight.emotion = emotion

        result = self.repo.update(highlight)
        if self.recommendation_service and highlight.user_id is not None:
            self.recommendation_service.invalidate_user(int(highlight.user_id))
        if self.highlight_dashboard_cache is not None:
            self.highlight_dashboard_cache.invalidate_public()
        return result
