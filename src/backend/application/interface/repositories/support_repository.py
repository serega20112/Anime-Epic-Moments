from abc import ABC, abstractmethod

from backend.domain.entities.support.support_ticket import SupportTicket


class SupportRepository(ABC):
    """Контракт хранилища тикетов поддержки."""

    @abstractmethod
    async def add(self, ticket: SupportTicket) -> SupportTicket:
        """Создает новый тикет поддержки."""

    @abstractmethod
    async def update(self, ticket: SupportTicket) -> SupportTicket:
        """Обновляет существующий тикет поддержки."""
