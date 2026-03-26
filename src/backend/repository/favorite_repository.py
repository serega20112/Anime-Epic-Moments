from abc import ABC, abstractmethod
from typing import List
from src.backend.domain.favorite.entity import Favorite


class FavoriteRepository(ABC):
    @abstractmethod
    def add(self, favorite: Favorite) -> Favorite:
        """Добавляет аниме в избранное"""

    @abstractmethod
    def remove(self, user_id: int, anime_id: int):
        """Удаляет аниме из избранного"""

    @abstractmethod
    def get_by_user(self, user_id: int) -> List[Favorite]:
        """Возвращает все избранные аниме пользователя"""
