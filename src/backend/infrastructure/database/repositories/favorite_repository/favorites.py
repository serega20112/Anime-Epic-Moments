"""Реализация репозитория: класс пакета и сборка mixin'ов по агрегатам."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain import Favorite
from backend.infrastructure.database.models import FavoriteModel
from backend.infrastructure.database.serialization import dump_genres, load_genres


class FavoriteRepository:
    """Доступ к данным избранного."""

    def __init__(self, session: AsyncSession):
        """Сохранить сессию запроса, через которую работает репозиторий."""
        self.session = session

    async def add(self, favorite: Favorite):
        """Сохранить новую запись избранного."""
        db_fav = FavoriteModel(
            user_id=favorite.user_id,
            anime_id=favorite.anime_id,
            title=favorite.title,
            description=favorite.description,
            cover_url=favorite.cover_url,
            genres_json=dump_genres(favorite.genres),
            original_title=favorite.original_title,
        )
        self.session.add(db_fav)
        await self.session.flush()
        favorite.added_at = db_fav.added_at
        return favorite

    async def remove(self, user_id: int, anime_id: int):
        """Удалить запись избранного пользователя."""
        result = await self.session.execute(
            select(FavoriteModel).where(
                FavoriteModel.user_id == user_id,
                FavoriteModel.anime_id == anime_id,
            )
        )
        db_fav = result.scalar_one_or_none()
        if db_fav:
            await self.session.delete(db_fav)
            await self.session.flush()

    async def get_by_user(self, user_id: int) -> list[Favorite]:
        """Вернуть избранное пользователя."""
        result = await self.session.execute(
            select(FavoriteModel).where(FavoriteModel.user_id == user_id)
        )
        return [
            Favorite(
                user_id=r.user_id,
                anime_id=r.anime_id,
                added_at=r.added_at,
                title=r.title,
                description=r.description,
                cover_url=r.cover_url,
                genres=load_genres(r.genres_json),
                original_title=r.original_title,
            )
            for r in result.scalars().all()
        ]

    async def get_favorite_ids(self, user_id: int) -> list[int]:
        """Вернуть только идентификаторы аниме из избранного."""
        result = await self.session.execute(
            select(FavoriteModel.anime_id).where(FavoriteModel.user_id == user_id)
        )
        return [int(anime_id) for anime_id in result.scalars().all()]
