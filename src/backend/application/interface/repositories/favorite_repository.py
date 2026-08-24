from abc import ABC, abstractmethod

from backend.domain.entities.favorite.favorite import Favorite


class FavoriteRepository(ABC):
    @abstractmethod
    async def add(self, favorite: Favorite) -> Favorite:
        """Добавляет аниме в избранное"""

    @abstractmethod
    async def remove(self, user_id: int, anime_id: int):
        """Удаляет аниме из избранного"""

    @abstractmethod
    async def get_by_user(self, user_id: int) -> list[Favorite]:
        """Возвращает все избранные аниме пользователя"""

    @abstractmethod
    async def get_favorite_ids(self, user_id: int) -> list[int]:
        """Возвращает только id избранных аниме пользователя"""
