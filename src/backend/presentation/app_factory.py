"""FastAPI application factory with middleware, security headers, and CSRF protection."""

from __future__ import annotations

import logging
import secrets
from http import HTTPStatus
from pathlib import Path
from time import perf_counter

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.config import Settings
from backend.events.lifecycle import lifespan
from backend.infrastructure.di.dishka_container import build_dishka_container
from backend.infrastructure.web import render_template
from backend.presentation.api.v1.anime_route import anime_router
from backend.presentation.api.v1.auth_route import auth_router
from backend.presentation.api.v1.collection_route import collection_router
from backend.presentation.api.v1.favorite_route import favorite_router
from backend.presentation.api.v1.health_route import health_router
from backend.presentation.api.v1.highlight_route import highlight_router
from backend.presentation.api.v1.index_route import index_router
from backend.presentation.api.v1.moment_route import moment_router, watch_moment_router
from backend.presentation.api.v1.reaction_route import reaction_router
from backend.presentation.api.v1.recommendation_route import recommendation_router
from backend.presentation.api.v1.support_route import support_router
from backend.presentation.api.v1.user_route import user_router
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
    wants_json,
)
from backend.utils.logging import request_id_var, user_id_var

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_ROOT = PROJECT_ROOT / "src" / "frontend"
logger = logging.getLogger("anime_epic_moments")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance.

    Initializes middleware, security headers, CSRF protection, exception handlers,
    and registers all route blueprints.

    Returns:
        FastAPI: Configured application instance.
    """
    app = FastAPI(debug=Settings.app_debug, lifespan=lifespan)
    dishka_container = build_dishka_container()
    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_ROOT / "static")),
        name="static",
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=Settings.secret_key,
        same_site=Settings.cookie_samesite.lower(),
        https_only=Settings.cookie_secure,
        session_cookie="aem_session",
    )

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        """Assign a request ID, correlate logs, and report latency.

        Returns:
            Response: HTTP response with the request ID header.
        """
        request_id = request.headers.get("X-Request-ID") or secrets.token_hex(8)
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

    @app.middleware("http")
    async def app_context_middleware(request: Request, call_next):
        """Process each HTTP request through middleware pipeline.

        Returns:
            Response: HTTP response.
        """
        if await request_too_large(request):
            return await request_too_large_response(request)

        request.state.db_session = None
        request.state.user = None
        request.state.clear_access_token_cookie = False
        request.state.csrf_token = None

        if await is_cross_origin_write_request(request):
            logger.warning(
                "cross_origin_write_blocked path=%s origin=%s referer=%s",
                request.url.path,
                request.headers.get("Origin"),
                request.headers.get("Referer"),
            )
            return JSONResponse(
                {"error": "forbidden_origin"},
                status_code=HTTPStatus.FORBIDDEN,
            )

        try:
            if not await is_scope_free_request(request):
                await load_user(request)
                await prepare_csrf_token(request)
            if request.method in {"POST", "PUT", "PATCH", "DELETE"} and not await is_csrf_exempt(
                request
            ):
                if not await validate_csrf(request):
                    logger.warning("csrf_validation_failed path=%s", request.url.path)
                    if await wants_json(request):
                        return JSONResponse(
                            {"error": "csrf_failed"},
                            status_code=HTTPStatus.FORBIDDEN,
                        )
                    return PlainTextResponse(
                        "CSRF validation failed",
                        status_code=HTTPStatus.FORBIDDEN,
                    )
            response = await call_next(request)
        finally:
            pass

        if getattr(request.state, "clear_access_token_cookie", False):
            await clear_cookie(response, "access_token")
        await apply_security_headers(response)
        return response

    app.include_router(auth_router)
    app.include_router(highlight_router)
    app.include_router(favorite_router)
    app.include_router(collection_router)
    app.include_router(anime_router)
    app.include_router(watch_router)
    app.include_router(watch_moment_router)
    app.include_router(reaction_router)
    app.include_router(moment_router)
    app.include_router(recommendation_router)
    app.include_router(support_router)
    app.include_router(user_router)
    app.include_router(index_router)
    app.include_router(health_router)

    @app.exception_handler(404)
    async def handle_not_found(request: Request, _error):
        """Handle 404 errors with a controlled response."""
        logger.warning("not_found path=%s", request.url.path)
        if await wants_json(request):
            return JSONResponse(
                {"error": "not_found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
        return await render_template(
            request,
            "errors/404.html",
            status_code=HTTPStatus.NOT_FOUND,
        )

    @app.exception_handler(Exception)
    async def handle_internal_error(request: Request, _error: Exception):
        """Handle unhandled exceptions with a controlled 500 response."""
        logger.exception("internal_server_error path=%s", request.url.path)
        if await wants_json(request):
            return JSONResponse(
                {"error": "internal_server_error"},
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        return await render_template(
            request,
            "errors/500_modal.html",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    setup_dishka(container=dishka_container, app=app)

    return app
