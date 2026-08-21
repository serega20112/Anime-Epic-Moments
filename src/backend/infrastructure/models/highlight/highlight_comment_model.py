"""SQLAlchemy-модель комментария к хайлайту."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from backend.infrastructure.files.database import Base


class HighlightCommentModel(Base):
    """Таблица ``highlight_comments``: обсуждение под хайлайтом."""

    __tablename__ = "highlight_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    highlight_id = Column(
        Integer, ForeignKey("highlights.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content = Column(String(600), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
