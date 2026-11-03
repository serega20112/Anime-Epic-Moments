"""SQLAlchemy-модель пользователя."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String

from backend.infrastructure.database.session import Base


class UserModel(Base):
    """Таблица ``users``: идентичность и профиль пользователя."""

    __tablename__ = "users"
    __table_args__ = (Index("ix_users_google_subject", "google_subject", unique=True),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String(20), nullable=False)
    password_hash = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    status = Column(String(80), nullable=True)
    show_watch_activity = Column(Boolean, nullable=False, default=True)
    show_recent_episodes = Column(Boolean, nullable=False, default=True)
    google_subject = Column(String(64), nullable=True)
    email_verified = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
