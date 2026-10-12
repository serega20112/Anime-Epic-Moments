from __future__ import annotations

from backend.application.interface.repositories.rating_repository import RatingRepository
from backend.domain import UserAnimeRating


class GetUserRatingsUseCase:
    """Возвращает оценки пользователя по аниме."""

    def __init__(self, rating_repo: RatingRepository):
        """Initialize the use case.

        Args:
            rating_repo: Rating repository port.
        """
        self.rating_repo = rating_repo

    async def execute(self, user_id: int) -> list[UserAnimeRating]:
        """Return ratings of a user.

        Args:
            user_id: User identifier.

        Returns:
            list[UserAnimeRating]: User ratings ordered by rating time.
        """
        return await self.rating_repo.get_by_user(user_id)
