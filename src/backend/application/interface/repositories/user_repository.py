"""Интерфейс репозитория для User агрегата.

Отделяет домен от конкретного хранилища (PostgreSQL / любой другой DB).
"""

from abc import ABC, abstractmethod

from backend.domain.aggregates.user.user import User


class UserRepository(ABC):
    @abstractmethod
    async def add(self, user: User) -> User:
        """Сохраняет нового пользователя и возвращает с id"""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Получает пользователя по email"""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        """Получает пользователя по id"""

    @abstractmethod
    async def update(self, user: User) -> User:
        """Обновляет существующего пользователя"""

    @abstractmethod
    async def update_password(self, user_id: int, password_hash: str) -> User:
        """Обновляет пароль существующего пользователя"""

    @abstractmethod
    async def get_by_ids(self, user_ids: list[int]) -> list[User]:
        """Возвращает пользователей по списку id."""

    @abstractmethod
    async def follow(self, follower_user_id: int, followed_user_id: int) -> bool:
        """Создает подписку пользователя на другого пользователя."""

    @abstractmethod
    async def unfollow(self, follower_user_id: int, followed_user_id: int) -> bool:
        """Удаляет подписку пользователя на другого пользователя."""

    @abstractmethod
    async def is_following(self, follower_user_id: int, followed_user_id: int) -> bool:
        """Проверяет, подписан ли пользователь на другого пользователя."""

    @abstractmethod
    async def get_follow_stats(self, user_id: int) -> tuple[int, int]:
        """Возвращает количество подписчиков и подписок пользователя."""

    @abstractmethod
    async def get_followed_user_ids(self, follower_user_id: int) -> list[int]:
        """Возвращает список id пользователей, на которых оформлена подписка."""

    @abstractmethod
    async def get_followed_users(self, follower_user_id: int, limit: int = 12) -> list[User]:
        """Возвращает пользователей, на которых оформлена подписка."""

    @abstractmethod
    async def get_followers(self, followed_user_id: int, limit: int = 12) -> list[User]:
        """Возвращает пользователей, которые подписаны на target-пользователя."""
