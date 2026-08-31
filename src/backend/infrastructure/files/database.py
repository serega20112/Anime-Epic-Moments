"""Async SQLAlchemy engine/session bootstrap."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from sqlalchemy import inspect, text
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
    """Create async SQLAlchemy engine for the configured driver."""
    engine_kwargs = {"echo": False}
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs["pool_pre_ping"] = True
    return create_async_engine(database_url, **engine_kwargs)


async def create_session_factory(
    db_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create async session factory bound to the engine."""
    return async_sessionmaker(
        bind=db_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
        class_=AsyncSession,
    )


async def get_engine() -> AsyncEngine:
    """Return process-wide async engine singleton."""
    global engine
    if engine is None:
        engine = await create_db_engine(Settings.database_url)
    return engine


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return process-wide async sessionmaker singleton."""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = await create_session_factory(await get_engine())
    return SessionLocal


async def init_db():
    """Initialize tables for development and tests (create_all + legacy columns)."""
    async_engine = await get_engine()
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.run_sync(_ensure_watch_source_columns)
        await connection.run_sync(_ensure_favorite_columns)
        await connection.run_sync(_ensure_highlight_columns)
        await connection.run_sync(_ensure_highlight_context_columns)
        await connection.run_sync(_ensure_collection_item_columns)
        await connection.run_sync(_ensure_support_ticket_columns)
    logger.info("tables_initialized")


async def verify_schema():
    """Verify migrations were applied; raise a clear error otherwise.

    Runs in production startup so a missing schema fails fast instead of
    producing opaque 500s on the first request.
    """
    async_engine = await get_engine()
    async with async_engine.connect() as connection:
        await connection.run_sync(_verify_schema_tables)
        logger.info("schema_verified")


def _verify_schema_tables(connection):
    """Check required tables exist on a sync connection (run_sync wrapper)."""
    inspector = inspect(connection)
    table_names = set(inspector.get_table_names())
    missing_tables = sorted(
        [table_name for table_name in Base.metadata.tables if table_name not in table_names]
    )
    if "alembic_version" not in table_names:
        raise RuntimeError(
            "Database schema is not initialized: 'alembic_version' table is missing. "
            "Run 'alembic upgrade head' before starting the application."
        )
    if missing_tables:
        raise RuntimeError(
            "Database schema is out of date: tables missing: {missing}. "
            "Run 'alembic upgrade head' before starting the application.".format(
                missing=", ".join(missing_tables)
            )
        )


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a request-scoped AsyncSession."""
    session_factory = await get_session_factory()
    async with session_factory() as session:
        yield session


def _ensure_watch_source_columns(connection):
    """Add legacy-compatible columns in watch_sources."""
    inspector = inspect(connection)
    if "watch_sources" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("watch_sources")}
    if "source_type" not in existing_columns:
        connection.execute(
            text(
                "ALTER TABLE watch_sources ADD COLUMN source_type VARCHAR NOT NULL DEFAULT 'stream'"
            )
        )


def _ensure_favorite_columns(connection):
    """Add snapshot columns to favorites for backward compatibility."""
    inspector = inspect(connection)
    if "favorites" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("favorites")}
    missing_columns = {
        "title": "ALTER TABLE favorites ADD COLUMN title VARCHAR",
        "original_title": "ALTER TABLE favorites ADD COLUMN original_title VARCHAR",
        "description": "ALTER TABLE favorites ADD COLUMN description VARCHAR",
        "cover_url": "ALTER TABLE favorites ADD COLUMN cover_url VARCHAR",
        "genres_json": "ALTER TABLE favorites ADD COLUMN genres_json VARCHAR",
    }
    for column_name, ddl in missing_columns.items():
        if column_name not in existing_columns:
            connection.execute(text(ddl))


def _ensure_highlight_columns(connection):
    """Add highlight columns used by newer UI flows."""
    inspector = inspect(connection)
    if "highlights" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("highlights")}
    missing_columns = {
        "title": "ALTER TABLE highlights ADD COLUMN title VARCHAR NOT NULL DEFAULT ''",
        "category": "ALTER TABLE highlights ADD COLUMN category VARCHAR",
        "views_count": "ALTER TABLE highlights ADD COLUMN views_count INTEGER NOT NULL DEFAULT 0",
        "original_title": "ALTER TABLE highlights ADD COLUMN original_title VARCHAR",
    }
    for column_name, ddl in missing_columns.items():
        if column_name not in existing_columns:
            connection.execute(text(ddl))


def _ensure_highlight_context_columns(connection):
    """Add legacy-compatible columns in highlight_contexts."""
    inspector = inspect(connection)
    if "highlight_contexts" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("highlight_contexts")}
    missing_columns = {
        "original_title": ("ALTER TABLE highlight_contexts ADD COLUMN original_title VARCHAR"),
    }
    for column_name, ddl in missing_columns.items():
        if column_name not in existing_columns:
            connection.execute(text(ddl))


def _ensure_collection_item_columns(connection):
    """Add legacy-compatible columns in anime_collection_items."""
    inspector = inspect(connection)
    if "anime_collection_items" not in inspector.get_table_names():
        return
    existing_columns = {
        column["name"] for column in inspector.get_columns("anime_collection_items")
    }
    missing_columns = {
        "original_title": ("ALTER TABLE anime_collection_items ADD COLUMN original_title VARCHAR"),
    }
    for column_name, ddl in missing_columns.items():
        if column_name not in existing_columns:
            connection.execute(text(ddl))


def _ensure_support_ticket_columns(connection):
    """Add support ticket delivery metadata columns."""
    inspector = inspect(connection)
    if "support_tickets" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("support_tickets")}
    missing_columns = {
        "channel": (
            "ALTER TABLE support_tickets ADD COLUMN channel VARCHAR NOT NULL DEFAULT 'telegram'"
        ),
    }
    for column_name, ddl in missing_columns.items():
        if column_name not in existing_columns:
            connection.execute(text(ddl))
