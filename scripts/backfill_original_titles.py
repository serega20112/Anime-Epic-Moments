"""Доношение `original_title` в snapshot-таблицах из обогащённых метаданных аниме.

Читает строки таблиц ``favorites``, ``anime_collection_items`` и ``highlight_contexts``,
у которых ``original_title IS NULL``, запрашивает аниме через
:class:`AnimeApiClient` и сохраняет ``title`` вместе с ``original_title``, чтобы
шаблоны могли показывать основное и оригинальное название.

Запуск из корня репозитория (нужны PostgreSQL и настройки из ``.env``)::

    $env:PYTHONPATH = "src"
    uv run python scripts/backfill_original_titles.py

Скрипт идемпотентен: повторный пропуск обрабатывает только строки с пустым
``original_title``. Строки, по которым внешний источник не ответил или вернул
неполные данные, остаются нетронутыми — причина пишется в лог на уровне DEBUG.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from backend.infrastructure.database.session import get_engine, get_session_factory
from backend.infrastructure.external.catalog.anime_api_client import AnimeApiClient

logger = logging.getLogger("anime_epic_moments.backfill_original_titles")

TARGET_TABLES = ("favorites", "anime_collection_items", "highlight_contexts")


async def _fetch_pending(session: AsyncSession, table: str) -> list[tuple[int, int]]:
    """Выбрать строки таблицы, которым нужен добор оригинального названия.

    Args:
        session: Активная сессия базы данных.
        table: Имя таблицы snapshot-данных.

    Returns:
        list[tuple[int, int]]: Пары «id строки, id аниме» с пустым `original_title`.
    """
    result = await session.execute(
        text(f"SELECT id, anime_id FROM {table} WHERE original_title IS NULL")
    )
    return [(int(row_id), int(anime_id)) for row_id, anime_id in result.all()]


async def _backfill_table(
    session: AsyncSession,
    client: AnimeApiClient,
    table: str,
) -> tuple[int, int]:
    """Дополнить одну таблицу и зафиксировать результат транзакцией.

    Args:
        session: Активная сессия базы данных.
        client: Клиент каталога аниме.
        table: Имя таблицы snapshot-данных.

    Returns:
        tuple[int, int]: Число найденных строк и число реально обновлённых.
    """
    pending = await _fetch_pending(session, table)
    updated = 0
    for row_id, anime_id in pending:
        try:
            anime = await client.get_by_id(anime_id)
        except Exception as error:
            logger.debug(
                "skip anime_id=%s in %s (lookup failed: %s)",
                anime_id,
                table,
                error.__class__.__name__,
            )
            continue
        if anime is None or not anime.title or not anime.original_title:
            continue
        await session.execute(
            text(
                f"UPDATE {table} SET title = :title, original_title = :original_title "
                "WHERE id = :row_id"
            ),
            {
                "title": anime.title,
                "original_title": anime.original_title,
                "row_id": row_id,
            },
        )
        updated += 1
    await session.commit()
    return len(pending), updated


async def _run() -> None:
    """Пройти все целевые таблицы и закрыть внешние соединения по завершении."""
    engine: AsyncEngine = await get_engine()
    session_factory = await get_session_factory()
    anime_client = AnimeApiClient()
    try:
        async with session_factory() as session:
            total_processed = 0
            total_updated = 0
            for table in TARGET_TABLES:
                processed, updated = await _backfill_table(session, anime_client, table)
                total_processed += processed
                total_updated += updated
                logger.info("table=%s processed=%d updated=%d", table, processed, updated)
            logger.info(
                "backfill done total_processed=%d total_updated=%d",
                total_processed,
                total_updated,
            )
    finally:
        await anime_client.aclose()
        await engine.dispose()


def main() -> None:
    """Точка входа: выполнить добор и завершить процесс."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
