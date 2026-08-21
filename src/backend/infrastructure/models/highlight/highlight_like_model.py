"""SQLAlchemy-модель лайка хайлайта."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint

from backend.infrastructure.files.database import Base


class HighlightLikeModel(Base):
    """Таблица ``highlight_likes``: лайк пользователя; уникальность пары."""

    __tablename__ = "highlight_likes"
    __table_args__ = (UniqueConstraint("highlight_id", "user_id", name="uq_highlight_like"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    highlight_id = Column(
        Integer, ForeignKey("highlights.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)
