"""Порт генерации и проверки CSRF-токенов.

presentation работает с токеном как со значением (значение + момент истечения) и
не должен знать, как именно он сравнивается: constant-time сравнение и срок
действия — деталь реализации.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime


class CSRFToken:
    """CSRF-токен со временем истечения."""

    def __init__(self, value: str, expires_at: datetime) -> None:
        """Создать токен.

        Args:
            value: Случайное значение токена.
            expires_at: Момент истечения токена.
        """
        self.value = value
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        """Проверить, истёк ли срок действия токена.

        Returns:
            bool: True, если токен больше недействителен.
        """
        return datetime.now(UTC) >= self.expires_at

    def to_session(self) -> dict[str, str]:
        """Представить токен для хранения в сессии.

        Returns:
            dict[str, str]: Сериализованный токен.
        """
        return {"value": self.value, "expires_at": self.expires_at.isoformat()}

    @classmethod
    def from_session(cls, raw: object) -> CSRFToken | None:
        """Восстановить токен из данных сессии.

        Строковое значение считается бессрочным намеренно: так читаются
        сессии, созданные до появления срока действия, и старая сессия не
        ломает запрос.

        Args:
            raw: Значение, ранее сохранённое в сессии.

        Returns:
            CSRFToken | None: Токен либо None для повреждённых данных.
        """
        if isinstance(raw, str) and raw:
            return cls(value=raw, expires_at=datetime.max.replace(tzinfo=UTC))
        if not isinstance(raw, dict):
            return None
        value = str(raw.get("value") or "")
        try:
            expires_at = datetime.fromisoformat(str(raw.get("expires_at") or ""))
        except ValueError:
            return None
        if not value or expires_at.tzinfo is None:
            return None
        return cls(value=value, expires_at=expires_at)


class CSRFServiceInterface(ABC):
    """Контракт генератора и валидатора CSRF-токенов."""

    @abstractmethod
    def generate_token(self) -> CSRFToken:
        """Создать новый токен со временем истечения.

        Returns:
            CSRFToken: Новый токен.
        """

    @abstractmethod
    def is_valid(self, token: CSRFToken | None, submitted: str | None) -> bool:
        """Проверить присланное значение против хранящегося токена.

        Args:
            token: Токен из сессии либо None.
            submitted: Значение, присланное клиентом.

        Returns:
            bool: True при совпадении и действующем сроке.
        """
