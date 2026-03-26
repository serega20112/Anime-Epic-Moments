from src.backend.repository.favorite_repository import FavoriteRepository


class RemoveFavoriteUseCase:
    def __init__(self, repo: FavoriteRepository):
        self.repo = repo

    def execute(self, user_id: int, anime_id: int):
        self.repo.remove(user_id, anime_id)
