from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.security.flask_protection import client_ip, rate_limit
from backend.infrastructure.security.rate_limiter import RateLimiter


@pytest.mark.unit
def test_client_ip_reads_x_forwarded_for():
    """Проверяем, что client_ip берет первый адрес из X-Forwarded-For."""
    app = FastAPI()

    @app.get("/")
    async def index(request: Request):
        return PlainTextResponse(client_ip(request))

    with TestClient(app) as client:
        response = client.get("/", headers={"X-Forwarded-For": "10.0.0.1, 10.0.0.2"})

    assert response.status_code == 200
    assert response.text == "10.0.0.1"


@pytest.mark.unit
def test_rate_limit_decorator_returns_429_after_limit():
    """Проверяем, что rate_limit возвращает 429 после превышения лимита."""
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret")
    container = SimpleNamespace(
        rate_limiter=RateLimiter(KeyValueStore(redis_url=None, namespace="test"))
    )

    @app.middleware("http")
    async def inject_container(request: Request, call_next):
        request.state.container = container
        return await call_next(request)

    @app.get("/limited")
    @rate_limit(
        scope="limited",
        limit=1,
        window_seconds=60,
    )
    async def limited(request: Request):
        return PlainTextResponse("ok")

    with TestClient(app) as client:
        first = client.get("/limited")
        second = client.get("/limited")

    assert first.status_code == 200
    assert second.status_code == 429
