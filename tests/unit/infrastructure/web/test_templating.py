from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.testclient import TestClient

from backend.infrastructure.web.templating import (
    flash,
    pop_flashed_messages,
    render_template,
)

_STATIC_DIR = Path(__file__).resolve().parents[4] / "src" / "frontend" / "static"


def _build_app() -> FastAPI:
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
    app.add_middleware(
        SessionMiddleware,
        secret_key="test-secret",
        same_site="lax",
        session_cookie="aem_session",
    )

    @app.get("/")
    async def index(request: Request):
        flash(request, "Hello!")
        return pop_flashed_messages(request)

    @app.get("/render")
    async def render(request: Request):
        return render_template(request, "errors/404.html", title="Test")

    @app.get("/item/{item_id}")
    async def item(request: Request, item_id: int):
        return {"item_id": item_id}

    return app


def test_flash_and_pop_roundtrip():
    app = _build_app()
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == ["Hello!"]


def test_render_template_returns_html():
    app = _build_app()
    with TestClient(app) as client:
        response = client.get("/render")
        assert response.status_code == 200
        assert "<html" in response.text
        assert "text/html" in response.headers["content-type"]


def test_template_request_proxy_path_and_referrer():
    app = _build_app()
    with TestClient(app) as client:
        headers = {"Referer": "https://example.com/prev"}
        res = client.get("/render", headers=headers)
        assert res.status_code == 200


def test_flash_requires_dict_session():
    from types import SimpleNamespace

    request = SimpleNamespace(scope={"session": "not-a-dict"})
    flash(request, "ignored")
    assert pop_flashed_messages(request) == []
