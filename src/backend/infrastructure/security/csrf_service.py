"""Реализация CSRF-токенов с ограниченным временем жизни.

Значение и момент истечения описаны портом :class:`CSRFToken`, здесь только
генерация случайного значения и сверка в постоянном времени.
"""

from __future__ import annotations

import logging
import secrets
from datetime import UTC, datetime, timedelta

from backend.application.interface.services.csrf_service import (
    CSRFServiceInterface,
    CSRFToken,
)

logger = logging.getLogger("anime_epic_moments")

TOKEN_LENGTH = 32
TOKEN_EXPIRE_MINUTES = 30

__all__ = ["CSRFService", "CSRFToken"]


class CSRFService(CSRFServiceInterface):
    """Генерирует CSRF-токены и проверяет их срок действия.

    Токен хранится в сессии как пара ``(значение, время истечения)`` в
    ISO-формате. Такая форма устраняет расхождение типов, из-за которого
    потребителям приходилось разбирать и словарь, и строку.
    """

    def __init__(
        self,
        token_length: int = TOKEN_LENGTH,
        token_expire_minutes: int = TOKEN_EXPIRE_MINUTES,
    ) -> None:
        """Создать генератор токенов.

        Args:
            token_length: Длина случайной части токена в байтах.
            token_expire_minutes: Время жизни токена в минутах.
        """
        self.token_length = token_length
        self.token_expire_minutes = token_expire_minutes

    def generate_token(self) -> CSRFToken:
        """Создать новый токен со временем истечения.

        Returns:
            CSRFToken: Новый токен.
        """
        return CSRFToken(
            value=secrets.token_urlsafe(self.token_length),
            expires_at=datetime.now(UTC) + timedelta(minutes=self.token_expire_minutes),
        )

    def is_valid(self, token: CSRFToken | None, submitted: str | None) -> bool:
        """Проверить токен в постоянном времени и по сроку действия.

        Args:
            token: Хранящийся в сессии токен либо None.
            submitted: Значение, присланное клиентом.

        Returns:
            bool: True, если значения совпадают и срок действия не истёк.
        """
        if token is None or not submitted:
            return False
        if token.is_expired():
            return False
        return secrets.compare_digest(token.value, submitted)
