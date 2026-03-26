from src.backend.repository.favorite_repository import FavoriteRepository
from src.backend.domain.favorite.entity import Favorite


class AddFavoriteUseCase:
    def __init__(self, repo: FavoriteRepository):
        self.repo = repo

    def execute(self, user_id: int, anime_id: int) -> Favorite:
        favorite = Favorite(user_id=user_id, anime_id=anime_id)
        return self.repo.add(favorite)
