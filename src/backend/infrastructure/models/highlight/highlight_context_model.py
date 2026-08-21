"""SQLAlchemy-модель watch-контекста хайлайта."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from backend.infrastructure.files.database import Base


class HighlightContextModel(Base):
    """Таблица ``highlight_contexts``: привязка хайлайта к источнику и переводу.

    Используется, чтобы шареная ссылка открывала тот же плеер и озвучку,
    в которых момент был создан.
    """

    __tablename__ = "highlight_contexts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    highlight_id = Column(
        Integer, ForeignKey("highlights.id", ondelete="CASCADE"), nullable=False, index=True
    )
    watch_source_id = Column(
        Integer, ForeignKey("watch_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    translation_id = Column(
        Integer, ForeignKey("translations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
