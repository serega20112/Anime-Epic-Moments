from __future__ import annotations

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from src.backend.presentation.security_helpers import is_csrf_exempt, validate_csrf

TEST_CSRF_TOKEN = "test-csrf-token"


class CsrfMiddleware(BaseHTTPMiddleware):
    """Схема проверки CSRF"""

    async def dispatch(self, request, call_next):
        if request.method == "POST" and not await is_csrf_exempt(request):
            if not await validate_csrf(request):
                return PlainTextResponse("csrf_failed", status_code=403)
        return await call_next(request)


async def setup_session(request):
    request.session["csrf_token"] = TEST_CSRF_TOKEN
    return PlainTextResponse("ok")


async def echo_form(request):
    form = await request.form()
    return JSONResponse({"title": form.get("title")})


def _make_app() -> Starlette:
    return Starlette(
        routes=[
            Route("/setup", setup_session, methods=["GET"]),
            Route("/echo", echo_form, methods=["POST"]),
        ],
        middleware=[
            Middleware(SessionMiddleware, secret_key="test-secret"),
            Middleware(CsrfMiddleware),
        ],
    )


@pytest.mark.unit
def test_validate_csrf_keeps_form_fields_for_downstream_route():
    """Проверяем, что после validate_csrf в мидлвари роут получает полную форму.

    Регрессия: validate_csrf вызывал request.form() напрямую, Starlette
    BaseHTTPMiddleware при этом потреблял stream и вниз уходил пустой body —
    все поля формы терялись (например, название коллекции приходило пустым
    и падала доменная валидация «от 1 до 80 символов»).
    """
    client = TestClient(_make_app())
    client.get("/setup")

    response = client.post(
        "/echo",
        data={"csrf_token": TEST_CSRF_TOKEN, "title": "Новая коллекция"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Новая коллекция"


@pytest.mark.unit
def test_validate_csrf_rejects_form_without_matching_token():
    """Проверяем, что форма с неверным csrf_token по-прежнему отклоняется."""
    client = TestClient(_make_app())
    client.get("/setup")

    response = client.post(
        "/echo",
        data={"csrf_token": "wrong-token", "title": "Новая коллекция"},
    )

    assert response.status_code == 403
