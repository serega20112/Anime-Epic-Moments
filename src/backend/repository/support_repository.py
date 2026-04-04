from abc import ABC, abstractmethod

from src.backend.domain.support.entity import SupportTicket


class SupportRepository(ABC):
    """Контракт хранилища тикетов поддержки."""

    @abstractmethod
    def add(self, ticket: SupportTicket) -> SupportTicket:
        """Создает новый тикет поддержки."""

    @abstractmethod
    def update(self, ticket: SupportTicket) -> SupportTicket:
        """Обновляет существующий тикет поддержки."""
