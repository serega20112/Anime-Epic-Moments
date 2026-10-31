from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient

from backend.application.interface.services import RateLimiterInterface
from backend.application.policies import ProxyTrustPolicy
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.security.rate_limiter import RateLimiter
from backend.presentation.api.rate_limit import rate_limit


class _FakeContainer:
    """Заменяет request-scoped контейнер dishka: отдаёт зависимости по типу."""

    def __init__(self, providers: dict[type, object]) -> None:
        """Сохраняет карту «тип -> экземпляр».

        Args:
            providers: Доступные для разрешения зависимости.
        """
        self._providers = providers

    async def get(self, dependency: type) -> object:
        """Разрешить зависимость по типу.

        Args:
            dependency: Запрашиваемый тип.

        Returns:
            object: Зарегистрированный экземпляр.

        Raises:
            KeyError: Тип не зарегистрирован.
        """
        return self._providers[dependency]


def _build_app(limiter: RateLimiter | None) -> FastAPI:
    """Собирает приложение с единственным ограниченным эндпоинтом.

    Args:
        limiter: Лимитер для контейнера запроса либо None, когда контейнер
            недоступен.

    Returns:
        FastAPI: Приложение с маршрутом ``/limited``.
    """
    app = FastAPI()
    container = (
        _FakeContainer(
            {
                RateLimiterInterface: limiter,
                ProxyTrustPolicy: ProxyTrustPolicy(trusted_proxies=()),
            }
        )
        if limiter is not None
        else None
    )

    @app.middleware("http")
    async def inject_container(request: Request, call_next):
        if container is not None:
            request.state.dishka_container = container
        return await call_next(request)

    @app.get("/limited")
    @rate_limit(scope="limited", limit=1, window_seconds=60)
    async def limited(request: Request):
        return PlainTextResponse("ok")

    return app


@pytest.mark.unit
def test_rate_limit_decorator_returns_429_after_limit():
    """Проверяем, что rate_limit возвращает 429 после превышения лимита."""
    app = _build_app(RateLimiter(KeyValueStore(redis_url=None, namespace="test")))

    with TestClient(app) as client:
        first = client.get("/limited")
        second = client.get("/limited")

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["Retry-After"]


@pytest.mark.unit
def test_rate_limit_decorator_fails_closed_without_limiter():
    """Проверяем, что rate_limit возвращает 503, когда лимитер недоступен."""
    app = _build_app(None)

    with TestClient(app) as client:
        response = client.get("/limited")

    assert response.status_code == 503
    assert response.json()["code"] == "rate_limiter_unavailable"
