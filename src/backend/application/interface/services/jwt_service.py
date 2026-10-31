"""Порт работы с JWT-токенами."""

from __future__ import annotations

from abc import ABC, abstractmethod


class JWTServiceInterface(ABC):
    """Создание и разбор JWT-токенов.

    Отказ разбора объявляется доменным ``InvalidTokenError``, а не исключением
    библиотеки: смена PyJWT не должна затрагивать сценарии.
    """

    @abstractmethod
    async def create_access_token(self, user_id: int) -> str:
        """Создать access-токен пользователя."""

    @abstractmethod
    async def create_refresh_token(self, user_id: int) -> str:
        """Создать refresh-токен пользователя."""

    @abstractmethod
    async def decode_token(self, token: str) -> int:
        """Разобрать access-токен и вернуть идентификатор пользователя."""

    @abstractmethod
    async def decode_refresh_token(self, token: str) -> int:
        """Разобрать refresh-токен и вернуть идентификатор пользователя."""

    @abstractmethod
    async def create_password_reset_token(self, user_id: int, expires_minutes: int) -> str:
        """Создать токен восстановления пароля."""

    @abstractmethod
    async def decode_password_reset_token(self, token: str) -> int:
        """Разобрать токен восстановления пароля и вернуть идентификатор пользователя."""

    @abstractmethod
    async def get_token_ttl_seconds(self, token: str, expected_type: str | None = None) -> int:
        """Получить остаток жизни токена в секундах."""
