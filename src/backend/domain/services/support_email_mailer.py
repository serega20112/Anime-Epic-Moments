"""Abstract support email mailer interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SupportEmailMailerInterface(ABC):
    """Interface for sending support ticket emails."""

    @abstractmethod
    async def send(self, ticket_data: dict[str, Any]) -> None:
        """Send a support ticket email.

        Args:
            ticket_data: Dictionary with ticket information.
        """
