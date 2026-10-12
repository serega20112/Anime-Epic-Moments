from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interface.repositories.rating_repository import (
    RatingRepository as RatingRepositoryInterface,
)
from backend.domain import UserAnimeRating
from backend.infrastructure.models import UserAnimeRatingModel


class RatingRepository(RatingRepositoryInterface):
    """Data access for user anime ratings."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, rating: UserAnimeRating) -> UserAnimeRating:
        """Create or update a rating for a user and anime.

        Args:
            rating: Rating aggregate to persist.

        Returns:
            UserAnimeRating: The persisted rating.
        """
        result = await self.session.execute(
            select(UserAnimeRatingModel).where(
                UserAnimeRatingModel.user_id == rating.user_id,
                UserAnimeRatingModel.anime_id == rating.anime_id,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.score = rating.score
            row.rated_at = rating.rated_at
            await self.session.flush()
            rating.rated_at = row.rated_at
            return rating
        row = UserAnimeRatingModel(
            user_id=rating.user_id,
            anime_id=rating.anime_id,
            score=rating.score,
            rated_at=rating.rated_at,
        )
        self.session.add(row)
        await self.session.flush()
        rating.rated_at = row.rated_at
        return rating

    async def remove(self, user_id: int, anime_id: int) -> None:
        """Delete a rating for a user and anime.

        Args:
            user_id: User identifier.
            anime_id: Anime identifier.
        """
        result = await self.session.execute(
            select(UserAnimeRatingModel).where(
                UserAnimeRatingModel.user_id == user_id,
                UserAnimeRatingModel.anime_id == anime_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is not None:
            await self.session.delete(row)
            await self.session.flush()

    async def get_by_user(self, user_id: int) -> list[UserAnimeRating]:
        """Return all ratings of a user.

        Args:
            user_id: User identifier.

        Returns:
            list[UserAnimeRating]: User ratings ordered by rating time.
        """
        result = await self.session.execute(
            select(UserAnimeRatingModel)
            .where(UserAnimeRatingModel.user_id == user_id)
            .order_by(UserAnimeRatingModel.rated_at.desc())
        )
        return [await self._to_entity(row) for row in result.scalars().all()]

    async def get_by_user_and_anime(self, user_id: int, anime_id: int) -> UserAnimeRating | None:
        """Return a single rating for a user and anime.

        Args:
            user_id: User identifier.
            anime_id: Anime identifier.

        Returns:
            UserAnimeRating | None: The rating or None when missing.
        """
        result = await self.session.execute(
            select(UserAnimeRatingModel).where(
                UserAnimeRatingModel.user_id == user_id,
                UserAnimeRatingModel.anime_id == anime_id,
            )
        )
        row = result.scalar_one_or_none()
        return await self._to_entity(row) if row else None

    async def get_user_rating(self, user_id: int, anime_id: int) -> int | None:
        """Return a user's rating score for a single anime.

        Args:
            user_id: User identifier.
            anime_id: Anime identifier.

        Returns:
            int | None: The score or None when the user has not rated the anime.
        """
        result = await self.session.execute(
            select(UserAnimeRatingModel.score).where(
                UserAnimeRatingModel.user_id == user_id,
                UserAnimeRatingModel.anime_id == anime_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _to_entity(row: UserAnimeRatingModel) -> UserAnimeRating:
        return UserAnimeRating(
            user_id=row.user_id,
            anime_id=row.anime_id,
            score=row.score,
            rated_at=row.rated_at,
        )
