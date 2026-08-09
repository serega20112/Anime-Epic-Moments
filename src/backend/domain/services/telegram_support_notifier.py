"""Abstract Telegram support notifier interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TelegramSupportNotifierInterface(ABC):
    """Interface for sending Telegram support notifications."""

    @abstractmethod
    async def notify(self, ticket_data: dict[str, Any]) -> None:
        """Send a Telegram notification about a support ticket.

        Args:
            ticket_data: Dictionary with ticket information.
        """
