from backend.application.interface.repositories.favorite_repository import FavoriteRepository


class GetFavoriteIdsUseCase:
    """Возвращает id избранных аниме пользователя (без внешних запросов)."""

    def __init__(self, repo: FavoriteRepository):
        self.repo = repo

    async def execute(self, user_id: int) -> list[int]:
        """Return favorite anime ids for a user.

        Args:
            user_id: User identifier.

        Returns:
            list[int]: Favorite anime identifiers.
        """
        return await self.repo.get_favorite_ids(user_id)
