from sqlalchemy.orm import Session
from src.backend.infrastructure.models.sqlalchemy_models import FavoriteModel
from src.backend.domain.favorite.entity import Favorite
from typing import List


class FavoriteRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, favorite: Favorite):
        db_fav = FavoriteModel(user_id=favorite.user_id, anime_id=favorite.anime_id)
        self.session.add(db_fav)
        self.session.commit()
        favorite.added_at = db_fav.added_at

    def remove(self, user_id: int, anime_id: int):
        db_fav = (
            self.session.query(FavoriteModel)
            .filter_by(user_id=user_id, anime_id=anime_id)
            .first()
        )
        if db_fav:
            self.session.delete(db_fav)
            self.session.commit()

    def get_by_user(self, user_id: int) -> List[Favorite]:
        rows = self.session.query(FavoriteModel).filter_by(user_id=user_id).all()
        return [
            Favorite(user_id=r.user_id, anime_id=r.anime_id, added_at=r.added_at)
            for r in rows
        ]
