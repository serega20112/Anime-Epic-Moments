import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from src.backend.infrastructure.repositories._async import repository_method
from src.backend.infrastructure.models.sqlalchemy_models import FavoriteModel
from src.backend.domain.favorite.entity import Favorite
from typing import List


class FavoriteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @repository_method
    def add(self, favorite: Favorite):
        db_fav = FavoriteModel(
            user_id=favorite.user_id,
            anime_id=favorite.anime_id,
            title=favorite.title,
            description=favorite.description,
            cover_url=favorite.cover_url,
            genres_json=self._dump_genres(favorite.genres),
        )
        self.session.add(db_fav)
        self.session.commit()
        favorite.added_at = db_fav.added_at
        return favorite

    @repository_method
    def remove(self, user_id: int, anime_id: int):
        db_fav = (
            self.session.query(FavoriteModel)
            .filter_by(user_id=user_id, anime_id=anime_id)
            .first()
        )
        if db_fav:
            self.session.delete(db_fav)
            self.session.commit()

    @repository_method
    def get_by_user(self, user_id: int) -> List[Favorite]:
        rows = self.session.query(FavoriteModel).filter_by(user_id=user_id).all()
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
            for r in rows
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
