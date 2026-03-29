from __future__ import annotations

from types import SimpleNamespace

import jwt
import pytest

from src.backend import create_app as create_app_module


def test_create_app_loads_user_from_cookie(monkeypatch, user_factory):
    """Проверяем, что before_request поднимает пользователя в g по access_token."""
    monkeypatch.setattr(create_app_module, "init_db", lambda: None)
    monkeypatch.setattr(create_app_module.Settings, "database_auto_init", True)
    monkeypatch.setattr(
        create_app_module,
        "JWTService",
        lambda: SimpleNamespace(decode_token=lambda token: 7),
    )
    from src.backend.dependencies import container as container_module

    monkeypatch.setattr(
        container_module,
        "container",
        SimpleNamespace(
            user_repository=SimpleNamespace(get_by_id=lambda user_id: user_factory(id=user_id)),
            token_blocklist=SimpleNamespace(is_revoked=lambda token: False),
        ),
    )
    app = create_app_module.create_app()

    @app.route("/_whoami")
    def _whoami():
        from flask import g

        return str(getattr(g.user, "id", "none"))

    client = app.test_client()
    client.set_cookie("access_token", "token")
    response = client.get("/_whoami")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "7"


def test_create_app_skips_revoked_access_token(monkeypatch):
    """Проверяем, что create_app не поднимает пользователя по отозванному access token."""
    monkeypatch.setattr(create_app_module, "init_db", lambda: None)
    monkeypatch.setattr(create_app_module.Settings, "database_auto_init", True)
    monkeypatch.setattr(
        create_app_module,
        "JWTService",
        lambda: SimpleNamespace(decode_token=lambda token: 7),
    )
    from src.backend.dependencies import container as container_module

    monkeypatch.setattr(
        container_module,
        "container",
        SimpleNamespace(
            user_repository=SimpleNamespace(get_by_id=lambda user_id: None),
            token_blocklist=SimpleNamespace(is_revoked=lambda token: True),
        ),
    )
    app = create_app_module.create_app()

    @app.route("/_whoami")
    def _whoami():
        from flask import g

        return str(getattr(g, "user", None))

    client = app.test_client()
    client.set_cookie("access_token", "token")
    response = client.get("/_whoami")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "None"


@pytest.mark.parametrize("accept_header, expected_status", [("application/json", 500), ("text/html", 500)])
def test_create_app_handles_internal_errors(accept_header, expected_status, monkeypatch):
    """Проверяем, что create_app возвращает корректный 500-ответ для JSON и HTML клиентов."""
    monkeypatch.setattr(create_app_module, "init_db", lambda: None)
    monkeypatch.setattr(create_app_module.Settings, "database_auto_init", True)
    app = create_app_module.create_app()

    @app.route("/_explode")
    def _explode():
        raise RuntimeError("boom")

    response = app.test_client().get("/_explode", headers={"Accept": accept_header})

    assert response.status_code == expected_status


def test_create_app_skips_init_db_when_auto_init_disabled(monkeypatch):
    """Проверяем, что create_app не вызывает init_db, если database_auto_init выключен."""
    calls = []
    monkeypatch.setattr(create_app_module, "init_db", lambda: calls.append("init"))
    monkeypatch.setattr(create_app_module.Settings, "database_auto_init", False)

    create_app_module.create_app()

    assert calls == []


def test_create_app_adds_security_headers(monkeypatch):
    """Проверяем, что create_app выставляет базовые security headers на ответах."""
    monkeypatch.setattr(create_app_module, "init_db", lambda: None)
    monkeypatch.setattr(create_app_module.Settings, "database_auto_init", False)
    app = create_app_module.create_app()

    response = app.test_client().get("/")
    csp = response.headers["Content-Security-Policy"]

    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "Content-Security-Policy" in response.headers
    assert "media-src 'self' https: blob:" in csp
    assert "worker-src 'self' blob:" in csp
    assert "frame-src 'self' https:" in csp


def test_create_app_clears_invalid_access_cookie_without_traceback(monkeypatch, caplog):
    """Проверяем, что create_app сбрасывает битый access token без warning traceback."""
    monkeypatch.setattr(create_app_module, "init_db", lambda: None)
    monkeypatch.setattr(create_app_module.Settings, "database_auto_init", False)
    monkeypatch.setattr(
        create_app_module,
        "JWTService",
        lambda: SimpleNamespace(
            decode_token=lambda token: (_ for _ in ()).throw(
                jwt.InvalidSignatureError("bad signature")
            )
        ),
    )
    from src.backend.dependencies import container as container_module

    monkeypatch.setattr(
        container_module,
        "container",
        SimpleNamespace(
            user_repository=SimpleNamespace(get_by_id=lambda user_id: None),
            token_blocklist=SimpleNamespace(is_revoked=lambda token: False),
        ),
    )
    app = create_app_module.create_app()

    client = app.test_client()
    client.set_cookie("access_token", "broken-token")
    response = client.get("/")

    assert response.status_code == 200
    assert "access_token=;" in "\n".join(response.headers.getlist("Set-Cookie"))
    assert all(record.levelname != "WARNING" for record in caplog.records)


def test_create_app_skips_access_token_processing_for_static_requests(monkeypatch):
    """Проверяем, что create_app не декодирует access token на static-запросах."""
    monkeypatch.setattr(create_app_module, "init_db", lambda: None)
    monkeypatch.setattr(create_app_module.Settings, "database_auto_init", False)
    decode_calls = []
    monkeypatch.setattr(
        create_app_module,
        "JWTService",
        lambda: SimpleNamespace(decode_token=lambda token: decode_calls.append(token)),
    )
    app = create_app_module.create_app()

    client = app.test_client()
    client.set_cookie("access_token", "token")
    response = client.get("/static/css/styles.css")

    assert response.status_code in {200, 304}
    assert decode_calls == []


def test_create_app_allows_write_requests_from_current_host_origin(monkeypatch):
    """Проверяем, что POST с origin текущего host не блокируется даже без совпадения с APP_BASE_URL."""
    monkeypatch.setattr(create_app_module, "init_db", lambda: None)
    monkeypatch.setattr(create_app_module.Settings, "database_auto_init", False)
    monkeypatch.setattr(
        create_app_module.Settings,
        "app_base_url",
        "http://127.0.0.1:5000",
    )
    monkeypatch.setattr(
        create_app_module.Settings,
        "app_allowed_origins",
        [],
    )
    app = create_app_module.create_app()

    @app.route("/_post-ok", methods=["POST"])
    def _post_ok():
        return "ok"

    response = app.test_client().post(
        "/_post-ok",
        base_url="http://192.168.0.111:5000",
        headers={"Origin": "http://192.168.0.111:5000"},
    )

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "ok"


def test_create_app_blocks_write_requests_from_foreign_origin(monkeypatch):
    """Проверяем, что POST с чужого origin остается заблокированным."""
    monkeypatch.setattr(create_app_module, "init_db", lambda: None)
    monkeypatch.setattr(create_app_module.Settings, "database_auto_init", False)
    monkeypatch.setattr(
        create_app_module.Settings,
        "app_base_url",
        "http://127.0.0.1:5000",
    )
    monkeypatch.setattr(
        create_app_module.Settings,
        "app_allowed_origins",
        [],
    )
    app = create_app_module.create_app()

    @app.route("/_post-forbidden", methods=["POST"])
    def _post_forbidden():
        return "ok"

    response = app.test_client().post(
        "/_post-forbidden",
        base_url="http://192.168.0.111:5000",
        headers={"Origin": "http://evil.example.com"},
    )

    assert response.status_code == 403
    assert response.get_json() == {"error": "forbidden_origin"}
