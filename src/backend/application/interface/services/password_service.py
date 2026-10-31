"""Порт хеширования и проверки паролей."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordServiceInterface(ABC):
    """Хеширование и проверка паролей."""

    @abstractmethod
    async def hash_password(self, plain_password: str) -> str:
        """Захешировать пароль в открытом виде."""

    @abstractmethod
    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверить пароль по сохранённому хешу."""
