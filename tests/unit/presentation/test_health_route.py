from __future__ import annotations

import pytest
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.application.interface.services import HealthCheckPort
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.health.health_check import ApplicationHealthCheck
from backend.presentation.api.v1.health import health_router


class _FakeSession:
    """Async-сессия, управляемо отвечающая на запрос проверки базы."""

    def __init__(self, error: Exception | None = None) -> None:
        """Сохранить ошибку, которую должен поднять запрос.

        Args:
            error: Исключение для имитации недоступной базы.
        """
        self.error = error

    async def __aenter__(self) -> _FakeSession:
        """Вернуть саму сессию.

        Returns:
            _FakeSession: Эта же сессия.
        """
        return self

    async def __aexit__(self, *args) -> None:
        """Ничего не делать при выходе из контекста.

        Args:
            *args: Параметры исключения контекстного менеджера.
        """

    async def execute(self, _statement) -> None:
        """Выполнить запрос проверки базы.

        Args:
            _statement: SQL-выражение, результат которого не используется.

        Raises:
            Exception: Исключение, переданное конструктором для имитации сбоя.
        """
        if self.error is not None:
            raise self.error


class _FakeFactory:
    """Фабрика сессий, возвращающая настроенную сессию-заглушку."""

    def __init__(self, error: Exception | None = None) -> None:
        """Сохранить сценарий поведения сессии.

        Args:
            error: Исключение, которое поднимет execute сессии.
        """
        self.error = error

    def __call__(self) -> _FakeSession:
        """Вернуть новую сессию-заглушку.

        Returns:
            _FakeSession: Сессия с заданным поведением.
        """
        return _FakeSession(self.error)


async def _failing_factory() -> _FakeFactory:
    """Вернуть фабрику сессий, где запрос завершается ошибкой.

    Returns:
        _FakeFactory: Фабрика с сохранённым исключением.
    """
    return _FakeFactory(error=RuntimeError("db down"))


async def _working_factory() -> _FakeFactory:
    """Вернуть исправную фабрику сессий.

    Returns:
        _FakeFactory: Фабрика, чьи запросы проходят.
    """
    return _FakeFactory()


class _HealthProvider(Provider):
    """Провайдер порта проверки готовности поверх заданной реализации."""

    def __init__(self, health_check: HealthCheckPort) -> None:
        """Сохранить реализацию пробы.

        Args:
            health_check: Проверяемый объект.
        """
        super().__init__()
        self._health_check = health_check

    @provide(scope=Scope.APP)
    def health_check(self) -> HealthCheckPort:
        """Отдать порт проверки готовности.

        Returns:
            HealthCheckPort: Реализация из конструктора провайдера.
        """
        return self._health_check


def _build_client(health_check: HealthCheckPort) -> TestClient:
    """Собрать приложение с health-роутами и переданной пробой.

    Args:
        health_check: Реализация порта проверки готовности.

    Returns:
        TestClient: Клиент для обращения к пробам.
    """
    app = FastAPI()
    app.include_router(health_router)
    container: AsyncContainer = make_async_container(_HealthProvider(health_check))
    setup_dishka(container=container, app=app)
    return TestClient(app)


@pytest.mark.unit
class TestHealthEndpoints:
    """Интеграционные тесты проб liveness и readiness."""

    def test_health_reports_ok(self):
        """Что тестируем: GET /health.
        Что передаём: любую реализацию пробы — liveness её не зовёт.
        Что ожидаем: 200 и ``{"status": "ok"}`` без обращения к зависимостям.
        """
        health_check = ApplicationHealthCheck(
            store=KeyValueStore(redis_url=None), session_factory_getter=_working_factory
        )
        with _build_client(health_check) as client:
            response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_ready_ok_when_database_and_memory_store_available(self):
        """Что тестируем: GET /ready при живой базе и выключенном Redis.
        Что передаём: исправную фабрику сессий и in-memory хранилище.
        Что ожидаем: 200 и отметки ``database=ok``, ``redis=disabled``.
        """
        health_check = ApplicationHealthCheck(
            store=KeyValueStore(redis_url=None), session_factory_getter=_working_factory
        )
        with _build_client(health_check) as client:
            response = client.get("/ready")

        assert response.status_code == 200
        assert response.json() == {
            "status": "ready",
            "checks": {"database": "ok", "redis": "disabled"},
        }

    def test_ready_fails_when_database_unreachable(self):
        """Что тестируем: GET /ready при недоступной базе.
        Что передаём: фабрику сессий, чей запрос бросает исключение.
        Что ожидаем: 503, статус unavailable и отметка database=unreachable.
        """
        health_check = ApplicationHealthCheck(
            store=KeyValueStore(redis_url=None), session_factory_getter=_failing_factory
        )
        with _build_client(health_check) as client:
            response = client.get("/ready")

        assert response.status_code == 503
        payload = response.json()
        assert payload["status"] == "unavailable"
        assert payload["checks"]["database"] == "unreachable"

    def test_ready_fails_when_redis_unreachable(self):
        """Что тестируем: GET /ready при настроенном, но упавшем Redis.
        Что передаём: хранилище с адресом несуществующего сервера.
        Что ожидаем: 503 и отметка redis=unreachable при живой базе.
        """
        store = KeyValueStore(redis_url="redis://127.0.0.1:1")

        async def _fail_ping() -> bool:
            """Имитировать отказ Redis.

            Returns:
                bool: Не возвращается — метод бросает исключение.

            Raises:
                OSError: Всегда, чтобы проверить обработку сбоя пробой.
            """
            raise OSError("redis down")

        store.ping = _fail_ping
        health_check = ApplicationHealthCheck(store=store, session_factory_getter=_working_factory)
        with _build_client(health_check) as client:
            response = client.get("/ready")

        assert response.status_code == 503
        assert response.json()["checks"]["redis"] == "unreachable"
