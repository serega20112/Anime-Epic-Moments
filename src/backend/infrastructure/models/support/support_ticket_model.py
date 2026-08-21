"""SQLAlchemy-модель тикета поддержки."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)

from backend.infrastructure.files.database import Base


class SupportTicketModel(Base):
    """Таблица ``support_tickets``: заявка в поддержку и статус доставки уведомления."""

    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    email = Column(String(254), nullable=False)
    username = Column(String(40), nullable=False)
    subject = Column(String(120), nullable=False)
    message = Column(String(4000), nullable=False)
    channel = Column(String(20), nullable=False, default="telegram")
    page_url = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="open")
    delivery_status = Column(String(20), nullable=False, default="pending")
    delivery_error = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
