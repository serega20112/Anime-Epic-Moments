"""
Инициализация базы данных и сессии
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.backend.dependencies.settings import Settings

Base = declarative_base()
engine = create_engine(Settings.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Инициализирует базу данных, создавая все таблицы
    """
    # Импортируем модели, чтобы они зарегистрировались в Base
    from src.backend.infrastructure.models.sqlalchemy_models import (
        FavoriteModel,
        HighlightContextModel,
        HighlightModel,
        TranslationModel,
        UserAnimeStatusModel,
        UserModel,
        ViewingSessionModel,
        WatchSourceModel,
    )

    Base.metadata.create_all(bind=engine)
    print("✓ Таблицы успешно созданы или уже существуют")


def get_session():
    """
    Получение сессии SQLAlchemy
    """
    return SessionLocal()
