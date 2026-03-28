"""
Инициализация базы данных и сессии
"""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.backend.dependencies.settings import Settings

Base = declarative_base()
engine: Engine | None = None
SessionLocal: sessionmaker | None = None


def create_db_engine(database_url: str) -> Engine:
    """Создает SQLAlchemy engine с настройками под конкретный драйвер."""
    engine_kwargs = {"echo": False}
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs["pool_pre_ping"] = True
    return create_engine(database_url, **engine_kwargs)


def create_session_factory(db_engine: Engine) -> sessionmaker:
    """Создает фабрику SQLAlchemy session для заданного engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


def get_engine() -> Engine:
    """Возвращает singleton SQLAlchemy engine для приложения."""
    global engine
    if engine is None:
        engine = create_db_engine(Settings.database_url)
    return engine


def get_session_factory() -> sessionmaker:
    """Возвращает singleton session factory для приложения."""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = create_session_factory(get_engine())
    return SessionLocal


def init_db():
    """
    Инициализирует базу данных, создавая все таблицы
    """
    from src.backend.infrastructure.models.sqlalchemy_models import (
        FavoriteModel,
        HighlightCommentModel,
        HighlightContextModel,
        HighlightLikeModel,
        HighlightModel,
        SavedHighlightModel,
        TranslationModel,
        UserAnimeStatusModel,
        UserModel,
        ViewingSessionModel,
        WatchSourceModel,
    )

    db_engine = get_engine()
    Base.metadata.create_all(bind=db_engine)
    _ensure_watch_source_columns(db_engine)
    _ensure_favorite_columns(db_engine)
    _ensure_highlight_columns(db_engine)
    print("✓ Таблицы успешно созданы или уже существуют")


def get_session():
    """
    Получение сессии SQLAlchemy
    """
    return get_session_factory()()


def _ensure_watch_source_columns(db_engine: Engine | None = None):
    """Добавляет недостающие колонки в watch_sources для обратной совместимости."""
    db_engine = db_engine or get_engine()
    inspector = inspect(db_engine)
    if "watch_sources" not in inspector.get_table_names():
        return
    existing_columns = {
        column["name"] for column in inspector.get_columns("watch_sources")
    }
    if "source_type" not in existing_columns:
        with db_engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE watch_sources "
                    "ADD COLUMN source_type VARCHAR NOT NULL DEFAULT 'stream'"
                )
            )


def _ensure_favorite_columns(db_engine: Engine | None = None):
    """Добавляет snapshot-колонки в favorites для офлайн-рендера карточек."""
    db_engine = db_engine or get_engine()
    inspector = inspect(db_engine)
    if "favorites" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("favorites")}
    missing_columns = {
        "title": "ALTER TABLE favorites ADD COLUMN title VARCHAR",
        "description": "ALTER TABLE favorites ADD COLUMN description VARCHAR",
        "cover_url": "ALTER TABLE favorites ADD COLUMN cover_url VARCHAR",
        "genres_json": "ALTER TABLE favorites ADD COLUMN genres_json VARCHAR",
    }
    statements = [
        ddl for column_name, ddl in missing_columns.items() if column_name not in existing_columns
    ]
    if not statements:
        return
    with db_engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _ensure_highlight_columns(db_engine: Engine | None = None):
    """Добавляет недостающие поля в highlights для новых карточек и шеринга."""
    db_engine = db_engine or get_engine()
    inspector = inspect(db_engine)
    if "highlights" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("highlights")}
    missing_columns = {
        "title": "ALTER TABLE highlights ADD COLUMN title VARCHAR NOT NULL DEFAULT ''",
        "category": "ALTER TABLE highlights ADD COLUMN category VARCHAR",
        "views_count": "ALTER TABLE highlights ADD COLUMN views_count INTEGER NOT NULL DEFAULT 0",
    }
    statements = [
        ddl for column_name, ddl in missing_columns.items() if column_name not in existing_columns
    ]
    if not statements:
        return
    with db_engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
