"""SQLAlchemy-модель уведомления мобильного клиента."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String

from backend.infrastructure.database.session import Base


class NotificationModel(Base):
    """Таблица ``notifications``: событие для центра уведомлений получателя."""

    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_id_created_at", "user_id", "created_at"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    kind = Column(String(length=32), nullable=False)
    text = Column(String(length=400), nullable=False)
    anime_id = Column(Integer, nullable=True)
    highlight_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
