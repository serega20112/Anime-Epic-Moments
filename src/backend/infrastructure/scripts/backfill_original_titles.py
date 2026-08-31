"""Backfill original_title on snapshot tables from enriched anime metadata.

Reads every row of ``favorites``, ``anime_collection_items`` and
``highlight_contexts`` where ``original_title IS NULL``, resolves the anime
via :class:`AnimeApiClient.get_by_id`, and stores the enriched ``title`` and
``original_title`` so templates can show both lines.

Usage::

    python -m backend.infrastructure.scripts.backfill_original_titles
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from backend.infrastructure.external.anime_api_client import AnimeApiClient
from backend.infrastructure.files.database import get_engine, get_session_factory

logger = logging.getLogger("anime_epic_moments.backfill_original_titles")

TARGET_TABLES = ("favorites", "anime_collection_items", "highlight_contexts")


async def _fetch_pending(session: AsyncSession, table: str) -> list[tuple[int, int]]:
    """Return (row_id, anime_id) pairs needing backfill for a table."""
    result = await session.execute(
        text(f"SELECT id, anime_id FROM {table} WHERE original_title IS NULL")
    )
    return [(int(row_id), int(anime_id)) for row_id, anime_id in result.all()]


async def _backfill_table(
    session: AsyncSession,
    client: AnimeApiClient,
    table: str,
) -> tuple[int, int]:
    """Backfill one table; returns (processed, updated)."""
    pending = await _fetch_pending(session, table)
    updated = 0
    for row_id, anime_id in pending:
        try:
            anime = await client.get_by_id(anime_id)
        except Exception:
            logger.debug("skip anime_id=%s in %s (lookup failed)", anime_id, table)
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
    engine: AsyncEngine = await get_engine()
    session_factory = await get_session_factory()
    anime_client = AnimeApiClient()
    try:
        async with session_factory() as session:
            session: AsyncSession
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
    """Entry point that runs the backfill and exits."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
