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

_NAV_ROUTE_NAMES = {
    "anime.search_anime_page": ("/anime/search", ("GET",)),
    "anime.catalog_page": ("/anime/catalog", ("GET",)),
    "anime.search_by_description_page": ("/anime/search/description", ("GET",)),
    "highlight.get_public_top_highlights": ("/highlights/top", ("GET",)),
    "highlight.get_highlight_feed": ("/highlights/feed", ("GET",)),
    "highlight.get_user_highlights": ("/highlights/{user_id}", ("GET",)),
    "highlight.get_liked_highlights": ("/highlights/liked", ("GET",)),
    "highlight.get_saved_highlights": ("/highlights/saved", ("GET",)),
    "highlight.get_highlight_notifications": ("/highlights/notifications", ("GET",)),
    "favorite.get_favorites": ("/favorites/{user_id}", ("GET",)),
    "collection.collections_page": ("/collections", ("GET",)),
    "collection.create_collection": ("/collections", ("POST",)),
    "auth.profile_page": ("/auth/profile", ("GET",)),
    "auth.login_page": ("/auth/login", ("GET",)),
    "auth.register_page": ("/auth/register", ("GET",)),
    "auth.logout_user": ("/auth/logout", ("POST",)),
    "auth.password_reset_request_page": ("/auth/password-reset", ("GET",)),
    "auth.confirm_password_reset": ("/auth/password-reset/confirm", ("POST",)),
    "support.support_page": ("/support", ("GET",)),
    "user.public_profile_page": ("/users/{user_id}", ("GET",)),
    "user.follow_user": ("/users/{user_id}/follow", ("POST",)),
    "user.unfollow_user": ("/users/{user_id}/unfollow", ("POST",)),
    "watch.watch_page": ("/watch/{anime_id}", ("GET",)),
    "collection.shared_collection_page": ("/collections/share/{collection_id}", ("GET",)),
}


def _register_placeholder(app: FastAPI, name: str, rule: str, methods: tuple[str, ...]) -> None:
    async def _placeholder(**_kwargs):
        return ""

    app.add_api_route(rule, _placeholder, methods=list(methods), name=name)


def _build_app() -> FastAPI:
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
    app.add_middleware(
        SessionMiddleware,
        secret_key="test-secret",
        same_site="lax",
        session_cookie="aem_session",
    )

    @app.get("/", name="index.index")
    async def index(request: Request):
        await flash(request, "Hello!")
        return await pop_flashed_messages(request)

    @app.get("/render")
    async def render(request: Request):
        return await render_template(request, "errors/404.html", title="Test")

    @app.get("/item/{item_id}")
    async def item(request: Request, item_id: int):
        return {"item_id": item_id}

    for name, (rule, methods) in _NAV_ROUTE_NAMES.items():
        _register_placeholder(app, name, rule, methods)

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


async def test_flash_requires_dict_session():
    from types import SimpleNamespace

    request = SimpleNamespace(scope={"session": "not-a-dict"})
    await flash(request, "ignored")
    assert await pop_flashed_messages(request) == []
