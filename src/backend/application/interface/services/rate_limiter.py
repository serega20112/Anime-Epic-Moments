"""Порт оконного ограничителя частоты запросов.

Счётчики — инфраструктурная забота (Redis или in-memory fallback), а решение о
том, разрешён ли запрос, нужно layer-ам выше. Поэтому контракт и тип результата
живут здесь: presentation обращается к :class:`RateLimiterInterface`, а не к
конкретному счётчику.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RateLimitDecision:
    """Результат проверки лимита запросов.

    Attributes:
        allowed: Разрешён ли запрос.
        current_count: Сколько запросов уже учтено в окне.
        remaining: Сколько запросов осталось в окне.
        retry_after: Через сколько секунд окно сдвинется.
    """

    allowed: bool
    current_count: int
    remaining: int
    retry_after: int


class RateLimiterInterface(ABC):
    """Контракт счётчика запросов в скользящем окне."""

    @abstractmethod
    async def hit(
        self,
        scope: str,
        subject: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        """Учесть запрос и вернуть решение по лимиту.

        Args:
            scope: Область ограничения.
            subject: Субъект ограничения.
            limit: Максимум запросов в окне.
            window_seconds: Размер окна в секундах.

        Returns:
            RateLimitDecision: Решение по текущему запросу.
        """

    @abstractmethod
    async def current(self, scope: str, subject: str) -> int:
        """Прочитать текущее значение счётчика, не увеличивая его.

        Args:
            scope: Область ограничения.
            subject: Субъект ограничения.

        Returns:
            int: Число запросов в текущем окне.
        """
