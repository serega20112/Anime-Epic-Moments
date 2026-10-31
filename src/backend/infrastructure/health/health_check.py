"""Проверка готовности: база через SELECT 1 и Redis через PING."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from sqlalchemy import text

from backend.application.interface.services.health_check import (
    DISABLED_MARK,
    OK_MARK,
    UNREACHABLE_MARK,
    HealthCheckPort,
    HealthStatus,
)
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.database.session import get_session_factory

logger = logging.getLogger("anime_epic_moments")

SessionFactoryGetter = Callable[[], Awaitable[Callable]]


class ApplicationHealthCheck(HealthCheckPort):
    """Опрашивает зависимости приложения и сводит результат в статус."""

    def __init__(
        self,
        store: KeyValueStore,
        session_factory_getter: SessionFactoryGetter = get_session_factory,
    ) -> None:
        """Указать проверяемые зависимости.

        Args:
            store: Общее хранилище ключ-значение (Redis или in-memory fallback).
            session_factory_getter: Фабрика async-сессий SQLAlchemy;
                параметризуется, чтобы тесты подменяли источник соединений.
        """
        self.store = store
        self.session_factory_getter = session_factory_getter

    async def check(self) -> HealthStatus:
        """Опросить базу и, если Redis настроен, сам Redis.

        Оба сбоя ловятся широко намеренно: проба готовности обязана ответить
        «не готов» вместо исключения, иначе оркестратор получит 500 вместо
        осмысленного 503. Причина отказа пишется в warning.

        Returns:
            HealthStatus: Совокупный статус и отметки по зависимостям.
        """
        checks: dict[str, str] = {}
        ready = True
        ready = await self._check_database(checks) and ready
        ready = await self._check_redis(checks) and ready
        return HealthStatus(ready=ready, checks=checks)

    async def _check_database(self, checks: dict[str, str]) -> bool:
        """Выполнить `SELECT 1` и записать результат в отметки.

        Args:
            checks: Словарь отметок, куда записывается результат.

        Returns:
            bool: True, если база ответила.
        """
        try:
            session_factory = await self.session_factory_getter()
            async with session_factory() as session:
                await session.execute(text("SELECT 1"))
        except Exception as error:
            logger.warning("health_database_unreachable reason=%s", error.__class__.__name__)
            checks["database"] = UNREACHABLE_MARK
            return False
        checks["database"] = OK_MARK
        return True

    async def _check_redis(self, checks: dict[str, str]) -> bool:
        """Проверить Redis и записать результат в отметки.

        Args:
            checks: Словарь отметок, куда записывается результат.

        Returns:
            bool: True, если Redis недоступен выключен или отвечает живым ping.
        """
        if not self.store.redis_configured:
            checks["redis"] = DISABLED_MARK
            return True
        try:
            alive = bool(await self.store.ping())
        except Exception as error:
            logger.warning("health_redis_unreachable reason=%s", error.__class__.__name__)
            checks["redis"] = UNREACHABLE_MARK
            return False
        checks["redis"] = OK_MARK if alive else UNREACHABLE_MARK
        return alive
