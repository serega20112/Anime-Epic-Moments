import json

from src.backend.repository.favorite_repository import FavoriteRepository
from src.backend.domain.favorite.entity import Favorite
from src.backend.services.recommendation_service import RecommendationService


class AddFavoriteUseCase:
    def __init__(
        self,
        repo: FavoriteRepository,
        recommendation_service: RecommendationService | None = None,
    ):
        self.repo = repo
        self.recommendation_service = recommendation_service

    def execute(
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
        result = self.repo.add(favorite)
        if self.recommendation_service:
            self.recommendation_service.invalidate_user(int(user_id))
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
