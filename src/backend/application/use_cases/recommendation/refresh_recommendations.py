from backend.domain import RecommendationResult
from backend.domain.services import (
    RecommendationServiceInterface as RecommendationService,
)


class RefreshRecommendationsUseCase:
    """Use case для обновления рекомендаций пользователя"""

    def __init__(self, service: RecommendationService):
        self.service = service

    async def execute(self, user_id: int, limit: int = 5) -> list[RecommendationResult]:
        """Генерирует новые рекомендации, игнорируя кэш"""
        return await self.service.generate(user_id, limit, force_refresh=True)
