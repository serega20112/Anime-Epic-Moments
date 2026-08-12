import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain import Favorite
from backend.infrastructure.models import FavoriteModel


class FavoriteRepository:
    """Data access for anime favorites."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, favorite: Favorite):
        """Persist a new favorite.

        Args:
            favorite: Favorite aggregate to persist.
        """
        db_fav = FavoriteModel(
            user_id=favorite.user_id,
            anime_id=favorite.anime_id,
            title=favorite.title,
            description=favorite.description,
            cover_url=favorite.cover_url,
            genres_json=self._dump_genres(favorite.genres),
        )
        self.session.add(db_fav)
        await self.session.commit()
        favorite.added_at = db_fav.added_at
        return favorite

    async def remove(self, user_id: int, anime_id: int):
        """Delete a favorite for a user and anime.

        Args:
            user_id: User identifier.
            anime_id: Anime identifier.
        """
        result = await self.session.execute(
            select(FavoriteModel).where(
                FavoriteModel.user_id == user_id,
                FavoriteModel.anime_id == anime_id,
            )
        )
        db_fav = result.scalar_one_or_none()
        if db_fav:
            await self.session.delete(db_fav)
            await self.session.commit()

    async def get_by_user(self, user_id: int) -> list[Favorite]:
        """Return favorites for a user.

        Args:
            user_id: User identifier.

        Returns:
            list[Favorite]: User favorites.
        """
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
                genres=self._load_genres(r.genres_json),
            )
            for r in result.scalars().all()
        ]

    def _dump_genres(self, genres: list[str] | None) -> str | None:
        if not genres:
            return None
        cleaned = [str(genre).strip() for genre in genres if str(genre).strip()]
        return json.dumps(cleaned, ensure_ascii=False) if cleaned else None

    def _load_genres(self, payload: str | None) -> list[str]:
        if not payload:
            return []
        try:
            data = json.loads(payload)
        except (TypeError, ValueError):
            return []
        if not isinstance(data, list):
            return []
        return [str(item).strip() for item in data if str(item).strip()]
