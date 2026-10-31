"""Реализация репозитория: класс пакета и сборка mixin'ов по агрегатам."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interface.repositories.rating_repository import (
    RatingRepository as RatingRepositoryInterface,
)
from backend.domain import UserAnimeRating
from backend.infrastructure.database.models import UserAnimeRatingModel


class RatingRepository(RatingRepositoryInterface):
    """Доступ к данным оценок аниме."""

    def __init__(self, session: AsyncSession):
        """Сохранить сессию запроса, через которую работает репозиторий."""
        self.session = session

    async def upsert(self, rating: UserAnimeRating) -> UserAnimeRating:
        """Создать или обновить оценку аниме пользователем."""
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
        """Удалить оценку аниме пользователем."""
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
        """Вернуть все оценки пользователя."""
        result = await self.session.execute(
            select(UserAnimeRatingModel)
            .where(UserAnimeRatingModel.user_id == user_id)
            .order_by(UserAnimeRatingModel.rated_at.desc())
        )
        return [await self._to_entity(row) for row in result.scalars().all()]

    async def get_by_user_and_anime(self, user_id: int, anime_id: int) -> UserAnimeRating | None:
        """Вернуть оценку пользователя для одного аниме."""
        result = await self.session.execute(
            select(UserAnimeRatingModel).where(
                UserAnimeRatingModel.user_id == user_id,
                UserAnimeRatingModel.anime_id == anime_id,
            )
        )
        row = result.scalar_one_or_none()
        return await self._to_entity(row) if row else None

    async def get_user_rating(self, user_id: int, anime_id: int) -> int | None:
        """Вернуть числовую оценку пользователя для одного аниме."""
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
