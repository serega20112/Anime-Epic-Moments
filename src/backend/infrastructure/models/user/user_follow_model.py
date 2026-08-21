"""SQLAlchemy-модель подписки пользователя на пользователя."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint

from backend.infrastructure.files.database import Base


class UserFollowModel(Base):
    """Таблица ``user_follows``: рёбра соцграфа «подписчик → автор»."""

    __tablename__ = "user_follows"
    __table_args__ = (
        UniqueConstraint("follower_user_id", "followed_user_id", name="uq_user_follow"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    follower_user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    followed_user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)
