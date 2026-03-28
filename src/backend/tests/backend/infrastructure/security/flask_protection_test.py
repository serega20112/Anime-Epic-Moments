from __future__ import annotations

from types import SimpleNamespace

from flask import Flask

from src.backend.infrastructure.cache.key_value_store import KeyValueStore
from src.backend.infrastructure.security.flask_protection import client_ip, rate_limit
from src.backend.infrastructure.security.rate_limiter import RateLimiter


def test_client_ip_reads_x_forwarded_for():
    """Проверяем, что client_ip берет первый адрес из X-Forwarded-For."""
    app = Flask(__name__)

    with app.test_request_context("/", headers={"X-Forwarded-For": "10.0.0.1, 10.0.0.2"}):
        assert client_ip() == "10.0.0.1"


def test_rate_limit_decorator_returns_429_after_limit():
    """Проверяем, что rate_limit возвращает 429 после превышения лимита."""
    app = Flask(__name__)
    app.secret_key = "test"
    container = SimpleNamespace(
        rate_limiter=RateLimiter(KeyValueStore(redis_url=None, namespace="test"))
    )

    @app.route("/limited")
    @rate_limit(
        container_getter=lambda: container,
        scope="limited",
        limit=1,
        window_seconds=60,
    )
    def limited():
        return "ok"

    client = app.test_client()
    first = client.get("/limited")
    second = client.get("/limited")

    assert first.status_code == 200
    assert second.status_code == 429
