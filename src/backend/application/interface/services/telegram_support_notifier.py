"""Порт уведомлений поддержки в Telegram."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TelegramSupportNotifierInterface(ABC):
    """Уведомления об обращениях в Telegram."""

    @abstractmethod
    async def notify(self, ticket_data: dict[str, Any]) -> None:
        """Отправить уведомление об обращении в Telegram."""
