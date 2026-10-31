"""Порт кэша дашбордов хайлайтов."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class HighlightDashboardCacheInterface(ABC):
    """Кэш подготовленных данных дашборда хайлайтов."""

    @abstractmethod
    async def get_dashboard(self, key: str) -> Any:
        """Прочитать дашборд из кэша."""

    @abstractmethod
    async def set_dashboard(self, key: str, data: Any, ttl_seconds: int | None = None) -> None:
        """Положить дашборд в кэш."""

    @abstractmethod
    async def invalidate(self, key: str | None = None) -> None:
        """Сбросить закэшированный дашборд."""
