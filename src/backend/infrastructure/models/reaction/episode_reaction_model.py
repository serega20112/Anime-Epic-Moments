"""SQLAlchemy-модель реакции на эпизод."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from backend.infrastructure.files.database import Base


class EpisodeReactionModel(Base):
    """Таблица ``episode_reactions``: реакция пользователя; одна на эпизод."""

    __tablename__ = "episode_reactions"
    __table_args__ = (
        UniqueConstraint("user_id", "anime_id", "episode", name="uq_episode_reaction"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    anime_id = Column(Integer, nullable=False)
    episode = Column(Integer, nullable=False)
    reaction_type = Column(String, nullable=False)
    timestamp = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
