"""SQLAlchemy-модель сохранённого хайлайта."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint

from backend.infrastructure.files.database import Base


class SavedHighlightModel(Base):
    """Таблица ``saved_highlights``: «сохранённое» пользователя."""

    __tablename__ = "saved_highlights"
    __table_args__ = (UniqueConstraint("highlight_id", "user_id", name="uq_saved_highlight"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    highlight_id = Column(
        Integer, ForeignKey("highlights.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    saved_at = Column(DateTime, default=datetime.utcnow)
