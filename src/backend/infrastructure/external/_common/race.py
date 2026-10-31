"""Гонка источников: первый непустой ответ выигрывает.

Каталог собирается из нескольких провайдеров одновременно. Если ждать
медленный источник, страница отдаётся по его таймауту; гонка же возвращает
первый пригодный ответ и отменяет остальные задачи, чтобы они не занимали
соединения.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from typing import Any, TypeVar

from backend.domain.value_objects.anime.catalog_page import CatalogPage

logger = logging.getLogger("anime_epic_moments")

_T = TypeVar("_T")


async def first_truthy(*awaitables: Awaitable[Any]) -> Any:
    """Дождаться первого истинного результата и отменить остальные задачи.

    Args:
        *awaitables: Корутины, участвующие в гонке.

    Returns:
        Any: Первое истинное значение или None, если все результаты ложные.
    """
    tasks = [asyncio.ensure_future(item) for item in awaitables]
    pending = list(tasks)
    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            value = _task_value(task)
            if value:
                for other in pending:
                    other.cancel()
                return value
    return None


async def first_catalog_page(*candidates: Awaitable[CatalogPage]) -> CatalogPage:
    """Дождаться первой непустой страницы каталога.

    Args:
        *candidates: Запросы страниц, участвующие в гонке.

    Returns:
        CatalogPage: Первая непустая страница или пустая страница, если ни
        один источник ничего не вернул.
    """
    tasks = [asyncio.ensure_future(item) for item in candidates]
    pending = list(tasks)
    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            value = _task_value(task)
            if value is not None and len(value):
                for other in pending:
                    other.cancel()
                return value
    return CatalogPage.build([], page=1, per_page=1, total=0)


def _task_value(task: asyncio.Future) -> Any:
    """Достать результат задачи, не роняя гонку из-за одного сбойного источника.

    Args:
        task: Завершённая задача.

    Returns:
        Any: Результат задачи либо None, если она завершилась исключением.
    """
    try:
        return task.result()
    except Exception as error:
        logger.debug("anime provider race call failed reason=%s", error.__class__.__name__)
        return None
