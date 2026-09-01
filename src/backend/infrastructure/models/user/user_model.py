"""SQLAlchemy-модель пользователя."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from backend.infrastructure.files.database import Base


class UserModel(Base):
    """Таблица ``users``: идентичность и профиль пользователя."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String(20), nullable=False)
    password_hash = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    status = Column(String(80), nullable=True)
    show_watch_activity = Column(Boolean, nullable=False, default=True)
    show_recent_episodes = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
