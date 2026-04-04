from sqlalchemy.orm import Session

from src.backend.domain.support.entity import SupportTicket
from src.backend.infrastructure.models.sqlalchemy_models import SupportTicketModel


class SupportRepository:
    """SQLAlchemy-репозиторий тикетов поддержки."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, ticket: SupportTicket) -> SupportTicket:
        """Сохраняет новый тикет поддержки в базе."""
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
        self.session.commit()
        return self._to_entity(db_ticket)

    def update(self, ticket: SupportTicket) -> SupportTicket:
        """Обновляет статус доставки существующего тикета."""
        db_ticket = self.session.query(SupportTicketModel).filter_by(id=ticket.id).first()
        if not db_ticket:
            raise ValueError("Тикет поддержки для обновления не найден")

        db_ticket.status = ticket.status
        db_ticket.channel = ticket.channel
        db_ticket.delivery_status = ticket.delivery_status
        db_ticket.delivery_error = ticket.delivery_error
        db_ticket.page_url = ticket.page_url
        self.session.commit()
        return self._to_entity(db_ticket)

    def _to_entity(self, db_ticket: SupportTicketModel) -> SupportTicket:
        """Преобразует SQLAlchemy-модель в доменную сущность."""
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
