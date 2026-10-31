"""Порт хранения кодов подтверждения адреса почты."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmailVerificationStoreInterface(ABC):
    """Хранилище кодов подтверждения адреса почты."""

    @abstractmethod
    async def generate_code(self, email: str, password: str, username: str, theme: str) -> str:
        """Сгенерировать и сохранить код подтверждения."""

    @abstractmethod
    async def verify_code(self, email: str, code: str) -> dict | None:
        """Проверить код и вернуть сохранённые данные регистрации."""

    @abstractmethod
    async def has_pending(self, email: str) -> bool:
        """Проверить, есть ли незавершённое подтверждение."""
