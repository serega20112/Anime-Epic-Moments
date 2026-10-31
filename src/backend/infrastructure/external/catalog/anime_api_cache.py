"""Кэш каталожных ответов ``AnimeApiClient``.

Каталог агрегирует несколько внешних API, поэтому ответы кэшируются по ключу
из параметров запроса. Сбой кэша не должен ломать выдачу: чтение и запись
деградируют в промах и в «значение не сохранено», а причина уходит в debug.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.domain.value_objects.anime.catalog_page import CatalogPage
from backend.infrastructure.cache.key_value_store import KeyValueStore

logger = logging.getLogger("anime_epic_moments")

CACHE_MISS = object()


class AnimeApiCache:
    """Обёртка над хранилищем ключ-значение для ответов каталога."""

    def __init__(self, store: KeyValueStore | None) -> None:
        """Инициализирует кэш.

        Args:
            store: Хранилище ключ-значение или None, если кэш выключен.
        """
        self.store = store

    async def key(self, *parts: object) -> str:
        """Собирает ключ кэша из частей запроса.

        Args:
            parts: Части ключа в порядке значимости.

        Returns:
            str: Ключ, разделённый двоеточиями.
        """
        return ":".join(str(part) for part in parts)

    async def get(self, key: str) -> Any:
        """Читает значение из кэша.

        Args:
            key: Ключ кэша.

        Returns:
            Any: Сохранённое значение либо :data:`CACHE_MISS`.
        """
        if self.store is None:
            return CACHE_MISS
        try:
            if not await self.store.contains(key):
                return CACHE_MISS
            return await self.store.get(key)
        except Exception as error:
            logger.debug("anime cache read failed reason=%s", error.__class__.__name__)
            return CACHE_MISS

    async def set(self, key: str, value: Any, ttl_seconds: int) -> Any:
        """Сохраняет значение в кэше и возвращает его вызывающей стороне.

        Args:
            key: Ключ кэша.
            value: Сохраняемое значение.
            ttl_seconds: Время жизни записи в секундах.

        Returns:
            Any: Переданное значение независимо от результата записи.
        """
        if self.store is None:
            return value
        try:
            await self.store.set(key, value, ttl_seconds=ttl_seconds)
        except Exception as error:
            logger.debug("anime cache write failed reason=%s", error.__class__.__name__)
        return value

    async def page(self, cached: Any, page: int, per_page: int) -> CatalogPage:
        """Восстанавливает страницу каталога из кэшированного payload'а.

        В кэше лежит словарь с ``items`` и ``total``; старые записи могли
        сохранить просто список тайтлов, поэтому поддерживаются обе формы.

        Args:
            cached: Значение из кэша.
            page: Запрошенный номер страницы.
            per_page: Запрошенный размер страницы.

        Returns:
            CatalogPage: Страница, собранная из кэша.
        """
        if isinstance(cached, dict):
            items = list(cached.get("items") or [])
            total = int(cached.get("total") or len(items))
            return CatalogPage.build(items, page=page, per_page=per_page, total=total)
        items = list(cached or [])
        return CatalogPage.build(items, page=page, per_page=per_page, total=len(items))
