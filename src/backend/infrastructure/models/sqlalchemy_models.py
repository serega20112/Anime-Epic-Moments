"""
SQLAlchemy модели для приложения
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from src.backend.infrastructure.files.database import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String(20), nullable=False)
    password_hash = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class HighlightModel(Base):
    __tablename__ = "highlights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    anime_id = Column(Integer, nullable=False)
    episode = Column(Integer, nullable=False)
    start_timestamp = Column(Float, nullable=False)
    end_timestamp = Column(Float, nullable=False)
    title = Column(String(120), nullable=False, default="")
    category = Column(String(40), nullable=True)
    description = Column(String, nullable=True)
    is_spoiler = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    likes_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    emotion = Column(String, nullable=True)


class HighlightLikeModel(Base):
    __tablename__ = "highlight_likes"
    __table_args__ = (
        UniqueConstraint("highlight_id", "user_id", name="uq_highlight_like"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    highlight_id = Column(Integer, ForeignKey("highlights.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class HighlightCommentModel(Base):
    __tablename__ = "highlight_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    highlight_id = Column(Integer, ForeignKey("highlights.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String(600), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SavedHighlightModel(Base):
    __tablename__ = "saved_highlights"
    __table_args__ = (
        UniqueConstraint("highlight_id", "user_id", name="uq_saved_highlight"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    highlight_id = Column(Integer, ForeignKey("highlights.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    saved_at = Column(DateTime, default=datetime.utcnow)


class FavoriteModel(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    anime_id = Column(Integer, nullable=False)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    cover_url = Column(String, nullable=True)
    genres_json = Column(String, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)


class UserAnimeStatusModel(Base):
    __tablename__ = "user_anime_statuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    anime_id = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TranslationModel(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    anime_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    translation_type = Column(String, nullable=False)
    language = Column(String, nullable=False, default="ru")
    created_at = Column(DateTime, default=datetime.utcnow)


class WatchSourceModel(Base):
    __tablename__ = "watch_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    anime_id = Column(Integer, nullable=False)
    episode = Column(Integer, nullable=False)
    translation_id = Column(Integer, ForeignKey("translations.id"), nullable=False)
    provider_name = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    stream_url = Column(String, nullable=False)
    quality_label = Column(String, nullable=False)
    source_type = Column(String, nullable=False, default="stream")
    created_at = Column(DateTime, default=datetime.utcnow)


class ViewingSessionModel(Base):
    __tablename__ = "viewing_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    anime_id = Column(Integer, nullable=False)
    episode = Column(Integer, nullable=False)
    watch_source_id = Column(Integer, ForeignKey("watch_sources.id"), nullable=False)
    position_seconds = Column(Float, nullable=False, default=0.0)
    volume = Column(Float, nullable=False, default=1.0)
    quality_label = Column(String, nullable=False)
    is_paused = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow)


class HighlightContextModel(Base):
    __tablename__ = "highlight_contexts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    highlight_id = Column(Integer, ForeignKey("highlights.id"), nullable=False)
    watch_source_id = Column(Integer, ForeignKey("watch_sources.id"), nullable=False)
    translation_id = Column(Integer, ForeignKey("translations.id"), nullable=False)
    title = Column(String, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
