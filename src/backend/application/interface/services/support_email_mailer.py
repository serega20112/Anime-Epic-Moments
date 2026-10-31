"""Порт отправки писем поддержки."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SupportEmailMailerInterface(ABC):
    """Отправка писем об обращениях в поддержку."""

    @abstractmethod
    async def send(self, ticket_data: dict[str, Any]) -> None:
        """Отправить письмо об обращении."""
