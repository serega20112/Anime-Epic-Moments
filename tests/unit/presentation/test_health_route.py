from __future__ import annotations

import pytest
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.presentation.api.v1 import health_route


class _FakeSession:
    """Session stub that optionally fails on execute."""

    def __init__(self, error: Exception | None = None):
        self.error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def execute(self, *args, **kwargs):
        if self.error is not None:
            raise self.error
        return None


class _FakeFactory:
    """Session factory stub returning a configurable session."""

    def __init__(self, error: Exception | None = None):
        self.error = error

    def __call__(self):
        return _FakeSession(self.error)


class _StoreProvider(Provider):
    def __init__(self, store: KeyValueStore) -> None:
        super().__init__()
        self._store = store

    @provide(scope=Scope.APP)
    def key_value_store(self) -> KeyValueStore:
        return self._store


@pytest.mark.unit
class TestHealthEndpoints:
    def _build_client(self, store: KeyValueStore):
        app = FastAPI()
        app.include_router(health_route.health_router)
        container: AsyncContainer = make_async_container(_StoreProvider(store))
        setup_dishka(container=container, app=app)
        return TestClient(app)

    def test_health_reports_ok(self):
        store = KeyValueStore(redis_url=None)
        with self._build_client(store) as client:
            response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_ready_ok_when_database_and_memory_store_available(self, monkeypatch):
        monkeypatch.setattr(health_route, "get_session_factory", lambda: _FakeFactory())
        store = KeyValueStore(redis_url=None)
        with self._build_client(store) as client:
            response = client.get("/ready")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ready",
            "checks": {"database": "ok", "redis": "disabled"},
        }

    def test_ready_fails_when_database_unreachable(self, monkeypatch):
        monkeypatch.setattr(
            health_route,
            "get_session_factory",
            lambda: _FakeFactory(error=RuntimeError("db down")),
        )
        store = KeyValueStore(redis_url=None)
        with self._build_client(store) as client:
            response = client.get("/ready")
        assert response.status_code == 503
        assert response.json()["status"] == "unavailable"
        assert response.json()["checks"]["database"] == "unreachable"

    def test_ready_fails_when_redis_unreachable(self, monkeypatch):
        monkeypatch.setattr(health_route, "get_session_factory", lambda: _FakeFactory())
        store = KeyValueStore(redis_url="redis://127.0.0.1:1")

        async def _fail_ping():
            raise OSError("redis down")

        store.ping = _fail_ping
        with self._build_client(store) as client:
            response = client.get("/ready")
        assert response.status_code == 503
        assert response.json()["checks"]["redis"] == "unreachable"
