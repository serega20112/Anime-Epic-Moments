from typing import List
from src.backend.domain.recommendation.value_object import RecommendationResult
from src.backend.services.recommendation_service import RecommendationService


class GenerateRecommendationsUseCase:
    def __init__(self, service: RecommendationService):
        self.service = service

    async def execute(self, user_id: int, limit: int = 5) -> List[RecommendationResult]:
        return await self.service.generate(user_id, limit)
