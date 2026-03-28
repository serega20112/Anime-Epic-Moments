from src.backend.repository.favorite_repository import FavoriteRepository
from src.backend.services.recommendation_service import RecommendationService


class RemoveFavoriteUseCase:
    def __init__(
        self,
        repo: FavoriteRepository,
        recommendation_service: RecommendationService | None = None,
    ):
        self.repo = repo
        self.recommendation_service = recommendation_service

    def execute(self, user_id: int, anime_id: int):
        self.repo.remove(user_id, anime_id)
        if self.recommendation_service:
            self.recommendation_service.invalidate_user(int(user_id))
