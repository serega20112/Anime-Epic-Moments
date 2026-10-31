"""Окружение Alembic: подключение метаданных схемы и выбор строки подключения.

Модуль используется всеми командами Alembic. Метаданные берутся из `Base`, а строка
подключения — из `Settings`, поэтому миграции всегда работают с той же схемой и тем же
прогоном, что и приложение. Импорты `backend.*` намеренно расположены ниже правки
`sys.path`: без неё пакет `src/backend` не был бы виден Alembic, поэтому эти строки
отмечены `noqa: E402`.
"""

from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path
from typing import Any

from alembic import context
from sqlalchemy import pool
from sqlalchemy.exc import NoSuchModuleError
from sqlalchemy.ext.asyncio import async_engine_from_config

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import backend.infrastructure.database.models  # noqa: F401,E402
from backend.config import Settings  # noqa: E402
from backend.infrastructure.database.session import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", Settings.database_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Выполнить миграции без активного соединения, генерируя SQL.

    Используется режимом `--sql`: Alembic печатает инструкции, опираясь на строку
    подключения и сравнение типов без обращения к базе.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Any) -> None:
    """Настроить контекст на переданное синхронное соединение и выполнить миграции.

    Args:
        connection: Синхронное соединение SQLAlchemy, полученное из async-движка.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Открыть async-движок из конфигурации и выполнить миграции поверх него.

    Raises:
        RuntimeError: Если async-драйвер БД не установлен — сообщение подсказывает,
            как добавить нужную зависимость.
    """
    configuration = config.get_section(config.config_ini_section, {})
    try:
        connectable = async_engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    except (ImportError, NoSuchModuleError) as exc:
        raise RuntimeError(
            "Не найден async-драйвер СУБД. Синхронизируйте окружение командой `uv sync` "
            "или добавьте драйвер: `uv add asyncpg` (PostgreSQL) / `uv add aiosqlite` (SQLite)."
        ) from exc

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Выполнить миграции через реальное подключение к базе."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
