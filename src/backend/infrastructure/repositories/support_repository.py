from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.support.entity import SupportTicket
from backend.infrastructure.models import SupportTicketModel


class SupportRepository:
    """Асинхронный SQLAlchemy-репозиторий тикетов поддержки."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, ticket: SupportTicket) -> SupportTicket:
        """Сохраняет новый тикет поддержки в базе.

        Args:
            ticket: Domен-сущность тикета для сохранения.

        Returns:
            SupportTicket: Сохранённый тикет.
        """
        db_ticket = SupportTicketModel(
            user_id=ticket.user_id,
            email=ticket.email,
            username=ticket.username,
            subject=ticket.subject,
            message=ticket.message,
            channel=ticket.channel,
            page_url=ticket.page_url,
            status=ticket.status,
            delivery_status=ticket.delivery_status,
            delivery_error=ticket.delivery_error,
        )
        self.session.add(db_ticket)
        await self.session.flush()
        return self._to_entity(db_ticket)

    async def update(self, ticket: SupportTicket) -> SupportTicket:
        """Обновляет статус доставки существующего тикета.

        Args:
            ticket: Тикет с обновлёнными полями.

        Returns:
            SupportTicket: Обновлённый тикет.
        """
        result = await self.session.execute(
            select(SupportTicketModel).where(SupportTicketModel.id == ticket.id)
        )
        db_ticket = result.scalar_one_or_none()
        if not db_ticket:
            raise ValueError("Тикет поддержки для обновления не найден")

        db_ticket.status = ticket.status
        db_ticket.channel = ticket.channel
        db_ticket.delivery_status = ticket.delivery_status
        db_ticket.delivery_error = ticket.delivery_error
        db_ticket.page_url = ticket.page_url
        await self.session.flush()
        return self._to_entity(db_ticket)

    def _to_entity(self, db_ticket: SupportTicketModel) -> SupportTicket:
        """Преобразует SQLAlchemy-модель в доменную сущность.

        Args:
            db_ticket: SQLAlchemy-модель.

        Returns:
            SupportTicket: Доменная сущность.
        """
        return SupportTicket(
            id=db_ticket.id,
            user_id=db_ticket.user_id,
            email=db_ticket.email,
            username=db_ticket.username,
            subject=db_ticket.subject,
            message=db_ticket.message,
            channel=db_ticket.channel,
            page_url=db_ticket.page_url,
            status=db_ticket.status,
            delivery_status=db_ticket.delivery_status,
            delivery_error=db_ticket.delivery_error,
            created_at=db_ticket.created_at,
        )
