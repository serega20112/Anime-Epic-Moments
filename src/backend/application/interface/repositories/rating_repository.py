from __future__ import annotations

from abc import ABC, abstractmethod

from backend.domain.entities.rating.anime_rating import UserAnimeRating


class RatingRepository(ABC):
    @abstractmethod
    async def upsert(self, rating: UserAnimeRating) -> UserAnimeRating:
        """Создает или обновляет оценку пользователя по аниме."""

    @abstractmethod
    async def remove(self, user_id: int, anime_id: int) -> None:
        """Удаляет оценку пользователя по аниме."""

    @abstractmethod
    async def get_by_user(self, user_id: int) -> list[UserAnimeRating]:
        """Возвращает все оценки пользователя."""

    @abstractmethod
    async def get_by_user_and_anime(self, user_id: int, anime_id: int) -> UserAnimeRating | None:
        """Возвращает оценку пользователя по конкретному аниме."""

    @abstractmethod
    async def get_user_rating(self, user_id: int, anime_id: int) -> int | None:
        """Возвращает оценку пользователя по конкретному аниме (значение)."""
