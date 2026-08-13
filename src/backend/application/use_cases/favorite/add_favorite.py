import json

from backend.domain import Favorite
from backend.domain import FavoriteRepository
from backend.domain.services import (
    RecommendationServiceInterface as RecommendationService,
)
from backend.domain.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.domain.unit_of_work import UnitOfWorkInterface


class AddFavoriteUseCase:
    def __init__(
            self,
            repo: FavoriteRepository,
            recommendation_service: RecommendationService | None = None,
            profile_overview_cache: ProfileOverviewCache | None = None,
            unit_of_work: UnitOfWorkInterface | None = None,
    ):
        self.repo = repo
        self.recommendation_service = recommendation_service
        self.profile_overview_cache = profile_overview_cache
        self.unit_of_work = unit_of_work

    async def execute(
            self,
            user_id: int,
            anime_id: int,
            title: str | None = None,
            description: str | None = None,
            cover_url: str | None = None,
            genres: list[str] | str | None = None,
    ) -> Favorite:
        """Add an anime to favorites within a transaction if configured."""
        if self.unit_of_work is None:
            return await self._execute(
                user_id, anime_id, title, description, cover_url, genres
            )
        async with self.unit_of_work:
            return await self._execute(
                user_id, anime_id, title, description, cover_url, genres
            )

    async def _execute(
            self,
            user_id: int,
            anime_id: int,
            title: str | None = None,
            description: str | None = None,
            cover_url: str | None = None,
            genres: list[str] | str | None = None,
    ) -> Favorite:
        favorite = Favorite(
            user_id=int(user_id),
            anime_id=int(anime_id),
            title=self._normalize_text(title),
            description=self._normalize_text(description),
            cover_url=self._normalize_text(cover_url),
            genres=self._normalize_genres(genres),
        )
        result = await self.repo.add(favorite)
        if self.recommendation_service:
            await self.recommendation_service.invalidate_user(int(user_id))
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_user(int(user_id), include_ai_summary=True)
        return result

    def _normalize_text(self, value: str | None) -> str | None:
        text = str(value or "").strip()
        return text or None

    def _normalize_genres(self, value: list[str] | str | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            try:
                parsed = json.loads(text)
            except ValueError:
                parsed = [part.strip() for part in text.split(",")]
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        return []
