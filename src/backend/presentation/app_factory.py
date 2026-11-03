"""Фабрика приложения FastAPI: middleware, заголовки безопасности и защита от CSRF."""

from __future__ import annotations

import logging
import re
import secrets
from http import HTTPStatus
from pathlib import Path
from time import perf_counter

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.config import Settings
from backend.events.lifecycle import lifespan
from backend.infrastructure.di.dishka_container import build_dishka_container
from backend.presentation.api.errors import (
    ERROR_REQUEST_TOO_LARGE,
    error_response,
    register_exception_handlers,
)
from backend.presentation.api.helpers import wants_json
from backend.presentation.api.v1.anime import anime_router, api_anime_router
from backend.presentation.api.v1.auth import api_auth_router, auth_router
from backend.presentation.api.v1.collections import api_collections_router, collection_router
from backend.presentation.api.v1.config import api_config_router
from backend.presentation.api.v1.favorites import favorite_router
from backend.presentation.api.v1.health import health_router
from backend.presentation.api.v1.highlights import api_highlights_router, highlight_router
from backend.presentation.api.v1.index import index_router
from backend.presentation.api.v1.moments import moment_router, watch_moment_router
from backend.presentation.api.v1.notifications import api_notifications_router
from backend.presentation.api.v1.ratings import rating_router
from backend.presentation.api.v1.reactions import reaction_router
from backend.presentation.api.v1.recommendations import recommendation_router
from backend.presentation.api.v1.support import support_router
from backend.presentation.api.v1.users import api_users_router, user_router
from backend.presentation.api.v1.watch_route import watch_router
from backend.presentation.security_helpers import (
    apply_security_headers,
    clear_cookie,
    is_cross_origin_write_request,
    is_csrf_exempt,
    is_scope_free_request,
    load_user,
    prepare_csrf_token,
    request_too_large,
    request_too_large_response,
    validate_csrf,
)
from backend.utils.logging import request_id_var, user_id_var

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_ROOT = PROJECT_ROOT / "src" / "frontend"
logger = logging.getLogger("anime_epic_moments")

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _normalize_request_id(raw_value: str | None) -> str:
    """Вернуть безопасный идентификатор запроса, сгенерировав новый при неверном вводе клиента."""
    candidate = str(raw_value or "").strip()
    if _REQUEST_ID_PATTERN.match(candidate):
        return candidate
    return secrets.token_hex(8)


class BodyLimitMiddleware:
    """ASGI-middleware, ограничивающая размер тела запроса."""

    def __init__(self, app, max_bytes: int) -> None:
        """Запомнить приложение и предельный размер тела запроса."""
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        """Обработать один вызов ASGI."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        received = 0
        response_started = False

        async def limited_receive():
            """Принять одно сообщение, прервав чтение при превышении предела."""
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _BodyTooLargeError()
            return message

        async def send_wrapper(message):
            """Отметить, что ответ уже начал отправляться."""
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, send_wrapper)
        except _BodyTooLargeError:
            if response_started:
                raise
            logger.warning("request_body_limit_exceeded path=%s", scope.get("path", ""))
            response = error_response(
                ERROR_REQUEST_TOO_LARGE,
                "Тело запроса слишком велико",
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            )
            await response(scope, receive, send)


class _BodyTooLargeError(Exception):
    """Превышение предела тела запроса в канале приёма."""


_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


async def _csrf_rejection(request: Request) -> Response:
    """Сформировать ответ отказа по CSRF в том формате, который ждёт клиент.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        Response: JSON с ``csrf_failed`` для API-клиентов и обычный текст для форм.
    """
    if wants_json(request):
        return error_response(
            "csrf_failed",
            "Проверка CSRF не пройдена",
            HTTPStatus.FORBIDDEN,
        )
    return PlainTextResponse(
        "CSRF validation failed",
        status_code=HTTPStatus.FORBIDDEN,
    )


async def app_context_middleware(request: Request, call_next) -> Response:
    """Подготовить контекст запроса, проверить безопасность и оформить ответ.

    Инициализирует состояния ``request.state`` (сессия БД, пользователь, флаги),
    отсекает слишком большие тела и кросс-ориджин записи, проверяет CSRF для
    запросов на запись и прогоняет итоговый ответ через
    :func:`apply_security_headers`, чтобы политика безопасности была единой во всех
    ветках, включая ранние отказы.

    Регрессия: ветка успешной CSRF-проверки обязана вызывать ``call_next``. Когда
    вместо этого `response` оставался не присвоенным, любой успешно прошедший CSRF
    POST (логин, регистрация, создание коллекции) падал с ``UnboundLocalError``.
    Поведение закреплено тестом
    ``tests/unit/presentation/test_app_context_middleware.py``.

    Args:
        request: Текущий HTTP-запрос.
        call_next: Передача управления следующему звену (маршруту).

    Returns:
        Response: Ответ маршрута либо ответ отказа.
    """
    request.state.db_session = None
    request.state.user = None
    request.state.clear_access_token_cookie = False
    request.state.csrf_token = None

    if await request_too_large(request):
        response = await request_too_large_response(request)
    elif await is_cross_origin_write_request(request):
        logger.warning(
            "cross_origin_write_blocked path=%s origin=%s referer=%s",
            request.url.path,
            request.headers.get("Origin"),
            request.headers.get("Referer"),
        )
        response = error_response(
            "forbidden_origin",
            "Запрос с чужого источника отклонён",
            HTTPStatus.FORBIDDEN,
        )
    else:
        if not await is_scope_free_request(request):
            await load_user(request)
            await prepare_csrf_token(request)
        csrf_required = request.method in _WRITE_METHODS and not await is_csrf_exempt(request)
        if csrf_required and not await validate_csrf(request):
            logger.warning("csrf_validation_failed path=%s", request.url.path)
            response = await _csrf_rejection(request)
        else:
            response = await call_next(request)

    if getattr(request.state, "clear_access_token_cookie", False):
        await clear_cookie(request, response, "access_token")
    await apply_security_headers(request, response)
    return response


def create_app() -> FastAPI:
    """Создать и настроить экземпляр приложения FastAPI.

    Подключает middleware, заголовки безопасности, защиту CSRF, лимит размера
    тела, обработчики исключений и все маршруты приложения.

    ``SessionMiddleware`` регистрируется последним намеренно: в Starlette
    последний добавленный middleware становится самым внешним и выполняется
    первым, поэтому ``request.scope["session"]`` уже доступен
    :func:`app_context_middleware` (``prepare_csrf_token`` /
    ``validate_csrf``) в момент его работы.

    Returns:
        FastAPI: Настроенный экземпляр приложения.
    """
    app = FastAPI(debug=Settings.app_debug, lifespan=lifespan)
    dishka_container = build_dishka_container()
    app.add_middleware(BodyLimitMiddleware, max_bytes=Settings.max_request_bytes)
    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_ROOT / "static")),
        name="static",
    )

    @app.middleware("http")
    async def static_revalidation_middleware(request: Request, call_next):
        """Требовать ревалидацию статики, чтобы деплой сразу доходил до пользователей."""
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers.setdefault("Cache-Control", "no-cache")
        return response

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        """Назначить идентификатор запроса, связать логи и замерить задержку."""
        request_id = _normalize_request_id(request.headers.get("X-Request-ID"))
        started_at = perf_counter()
        request_id_var.set(request_id)
        logger.info(
            "request_started method=%s path=%s",
            request.method,
            request.url.path,
        )
        try:
            response = await call_next(request)
        finally:
            request_id_var.set(None)
            user_id_var.set(None)
        duration_ms = int((perf_counter() - started_at) * 1000)
        response.headers.setdefault("X-Request-ID", request_id)
        logger.info(
            "request_finished method=%s path=%s status=%s duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    app.middleware("http")(app_context_middleware)

    app.add_middleware(
        SessionMiddleware,
        secret_key=Settings.secret_key,
        same_site=Settings.cookie_samesite.lower(),
        https_only=Settings.cookie_secure,
        session_cookie="aem_session",
    )

    app.include_router(auth_router)
    app.include_router(api_auth_router)
    app.include_router(api_config_router)
    app.include_router(api_anime_router)
    app.include_router(api_users_router)
    app.include_router(api_collections_router)
    app.include_router(api_highlights_router)
    app.include_router(api_notifications_router)
    app.include_router(highlight_router)
    app.include_router(favorite_router)
    app.include_router(collection_router)
    app.include_router(anime_router)
    app.include_router(watch_router)
    app.include_router(watch_moment_router)
    app.include_router(reaction_router)
    app.include_router(rating_router)
    app.include_router(moment_router)
    app.include_router(recommendation_router)
    app.include_router(support_router)
    app.include_router(user_router)
    app.include_router(index_router)
    app.include_router(health_router)

    register_exception_handlers(app)
    setup_dishka(container=dishka_container, app=app)

    return app
