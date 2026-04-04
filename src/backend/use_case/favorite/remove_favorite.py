from src.backend.repository.favorite_repository import FavoriteRepository
from src.backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from src.backend.services.recommendation_service import RecommendationService


class RemoveFavoriteUseCase:
    def __init__(
        self,
        repo: FavoriteRepository,
        recommendation_service: RecommendationService | None = None,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.repo = repo
        self.recommendation_service = recommendation_service
        self.profile_overview_cache = profile_overview_cache

    async def execute(self, user_id: int, anime_id: int):
        await self.repo.remove(user_id, anime_id)
        if self.recommendation_service:
            await self.recommendation_service.invalidate_user(int(user_id))
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_user(int(user_id), include_ai_summary=True)
