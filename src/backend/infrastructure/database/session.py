"""Инициализация и проверка схемы: движок, фабрика сессий, `Base`, состояние БД.

Модуль отвечает за подключение к базе данных и за то, чтобы запущенное приложение
работало со схемой, описанной миграциями Alembic. Исторически здесь же выполнялись
`ALTER TABLE` «для совместимости со старыми базами» — это создавало второй источник
истины о схеме в обход Alembic, поэтому удалено: расхождения теперь проверяются
:func:`verify_schema` и останавливают запуск с внятной ошибкой.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from backend.config import Settings

logger = logging.getLogger("anime_epic_moments")

Base = declarative_base()
engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


async def create_db_engine(database_url: str) -> AsyncEngine:
    """Создать async-движок SQLAlchemy под выбранный драйвер.

    Args:
        database_url: Строка подключения с async-схемой драйвера.

    Returns:
        AsyncEngine: Движок с настройками, специфичными для sqlite или PostgreSQL.
    """
    engine_kwargs: dict[str, object] = {"echo": False}
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs["pool_pre_ping"] = True
    return create_async_engine(database_url, **engine_kwargs)


async def create_session_factory(
    db_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Создать фабрику async-сессий, привязанную к движку.

    Args:
        db_engine: Движок, к которому привязываются сессии.

    Returns:
        async_sessionmaker: Фабрика сессий без автофлаша и автокоммита.
    """
    return async_sessionmaker(
        bind=db_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
        class_=AsyncSession,
    )


async def get_engine() -> AsyncEngine:
    """Вернуть общепроцессный синглтон движка, создав его при первом обращении.

    Returns:
        AsyncEngine: Движок для `Settings.database_url`.
    """
    global engine
    if engine is None:
        engine = await create_db_engine(Settings.database_url)
    return engine


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Вернуть общепроцессную фабрику сессий, создав её при первом обращении.

    Returns:
        async_sessionmaker: Фабрика, привязанная к :func:`get_engine`.
    """
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = await create_session_factory(await get_engine())
    return SessionLocal


async def init_db() -> None:
    """Создать таблицы из метаданных моделей — только для локальной разработки.

    Вызывается при `DATABASE_AUTO_INIT=1`. Это удобное зеркало моделей, а не механизм
    миграций: историю версий он не ведёт, поэтому в контейнере флаг закреплён в `0`,
    а схема создаётся `alembic upgrade head`. Изменения структуры таблиц здесь
    намеренно отсутствуют — они принадлежат миграциям.
    """
    async_engine = await get_engine()
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    logger.info("tables_initialized")


async def verify_schema() -> None:
    """Проверить, что применённая миграциями схема совпадает с моделями.

    Запускается на старте приложения: отсутствующие таблицы или колонки приводят к
    ошибке запуска вместо непрозрачных 500 на первом же запросе к ним.

    Raises:
        RuntimeError: Если не таблицы `alembic_version`, или в базе отсутствуют
            таблицы либо колонки, описанные метаданными моделей.
    """
    async_engine = await get_engine()
    async with async_engine.connect() as connection:
        await connection.run_sync(_verify_schema_tables)
        logger.info("schema_verified")


def get_schema_drift(connection) -> tuple[list[str], dict[str, list[str]]]:
    """Сравнить метаданные моделей с фактической структурой базы.

    Args:
        connection: Синхронное соединение SQLAlchemy (вызывается через `run_sync`).

    Returns:
        tuple[list[str], dict[str, list[str]]]: Отсутствующие таблицы и словарь
        «таблица -> отсутствующие колонки» для таблиц, которые в базе есть.
    """
    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())
    missing_tables = sorted(
        table_name for table_name in Base.metadata.tables if table_name not in existing_tables
    )
    missing_columns: dict[str, list[str]] = {}
    for table_name, table in Base.metadata.tables.items():
        if table_name not in existing_tables:
            continue
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        absent = sorted(
            column.name for column in table.columns if column.name not in existing_columns
        )
        if absent:
            missing_columns[table_name] = absent
    return missing_tables, missing_columns


def _verify_schema_tables(connection) -> None:
    """Проверить таблицы и колонки на синхронном соединении, подняв ошибку при расхождении.

    Args:
        connection: Синхронное соединение SQLAlchemy.

    Raises:
        RuntimeError: Схема не соответствует моделям или не имеет версии Alembic.
    """
    inspector = inspect(connection)
    table_names = set(inspector.get_table_names())
    if "alembic_version" not in table_names:
        raise RuntimeError(
            "Схема базы не инициализирована: отсутствует таблица 'alembic_version'. "
            "Перед запуском выполните 'alembic upgrade head'."
        )
    missing_tables, missing_columns = get_schema_drift(connection)
    if missing_tables:
        raise RuntimeError(
            "Схема базы устарела, отсутствуют таблицы: {missing}. "
            "Выполните 'alembic upgrade head' перед запуском приложения.".format(
                missing=", ".join(missing_tables)
            )
        )
    if missing_columns:
        detail = "; ".join(
            f"{table_name}: {', '.join(columns)}" for table_name, columns in missing_columns.items()
        )
        raise RuntimeError(
            f"Схема базы устарела, отсутствуют колонки ({detail}). "
            "Создайте и примените миграцию Alembic."
        )


async def get_session() -> AsyncIterator[AsyncSession]:
    """Отдать запрос-скоуповую сессию SQLAlchemy как зависимость FastAPI.

    Yields:
        AsyncSession: Сессия, закрытая по завершении обработки запроса.
    """
    session_factory = await get_session_factory()
    async with session_factory() as session:
        yield session
