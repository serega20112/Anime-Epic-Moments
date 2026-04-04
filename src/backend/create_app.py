from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlparse

import jwt
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from src.backend.delivery.api.v1.anime_route import anime_router
from src.backend.delivery.api.v1.auth_route import auth_router
from src.backend.delivery.api.v1.collection_route import collection_router
from src.backend.delivery.api.v1.favorite_route import favorite_router
from src.backend.delivery.api.v1.highlight_route import highlight_router
from src.backend.delivery.api.v1.index_route import index_router
from src.backend.delivery.api.v1.recommendation_route import recommendation_router
from src.backend.delivery.api.v1.support_route import support_router
from src.backend.delivery.api.v1.user_route import user_router
from src.backend.delivery.api.v1.watch_route import (
    close_watch_route_clients,
    watch_router,
)
from src.backend.dependencies import container as container_module
from src.backend.dependencies.settings import Settings
from src.backend.infrastructure.files.database import get_session_factory, init_db
from src.backend.infrastructure.security.jwt_service import JWTService
from src.backend.infrastructure.web.templating import render_template

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = PROJECT_ROOT / "src" / "frontend"
logger = logging.getLogger("anime_epic_moments")


def create_app() -> FastAPI:
    app = FastAPI(debug=Settings.flask_debug)
    app.state.root_container = container_module.container
    app.mount("/static", StaticFiles(directory=str(FRONTEND_ROOT / "static")), name="static")
    app.add_middleware(
        SessionMiddleware,
        secret_key=Settings.secret_key,
        same_site=Settings.cookie_samesite.lower(),
        https_only=Settings.cookie_secure,
        session_cookie="aem_session",
    )

    @app.on_event("startup")
    async def startup():
        if Settings.database_auto_init:
            await init_db()

    @app.on_event("shutdown")
    async def shutdown():
        await close_watch_route_clients()
        await app.state.root_container.shutdown()

    @app.middleware("http")
    async def app_context_middleware(request: Request, call_next):
        if _request_too_large(request):
            return _request_too_large_response(request)

        request.state.db_session = None
        request.state.container = _build_request_container(
            app.state.root_container,
            request_state=request.state,
        )
        request.state.user = None
        request.state.clear_access_token_cookie = False

        if _is_cross_origin_write_request(request):
            logger.warning(
                "cross_origin_write_blocked path=%s origin=%s referer=%s",
                request.url.path,
                request.headers.get("Origin"),
                request.headers.get("Referer"),
            )
            return JSONResponse({"error": "forbidden_origin"}, status_code=403)

        try:
            if not _is_scope_free_request(request):
                await _load_user(request)
            response = await call_next(request)
        finally:
            close = getattr(request.state.container, "aclose", None)
            if close is not None:
                await close()

        if getattr(request.state, "clear_access_token_cookie", False):
            _clear_cookie(response, "access_token")
        _apply_security_headers(response)
        return response

    @app.exception_handler(Exception)
    async def handle_internal_error(request: Request, _error: Exception):
        logger.exception("internal_server_error path=%s", request.url.path)
        if _wants_json(request):
            return JSONResponse({"error": "internal_server_error"}, status_code=500)
        return render_template(request, "errors/500_modal.html", status_code=500)

    app.include_router(auth_router)
    app.include_router(highlight_router)
    app.include_router(favorite_router)
    app.include_router(collection_router)
    app.include_router(anime_router)
    app.include_router(watch_router)
    app.include_router(recommendation_router)
    app.include_router(support_router)
    app.include_router(user_router)
    app.include_router(index_router)

    return app


async def _load_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return

    try:
        scoped_container = request.state.container
        token_blocklist = getattr(scoped_container, "token_blocklist", None)
        if token_blocklist is not None and await token_blocklist.is_revoked(token):
            logger.info("revoked_access_token_used path=%s", request.url.path)
            request.state.clear_access_token_cookie = True
            return
        jwt_service = getattr(scoped_container, "jwt_service", None) or JWTService()
        user_id = jwt_service.decode_token(token)
        request.state.user = await scoped_container.user_repository.get_by_id(user_id)
    except jwt.InvalidTokenError as error:
        logger.info(
            "access_token_rejected reason=%s path=%s",
            error.__class__.__name__,
            request.url.path,
        )
        request.state.clear_access_token_cookie = True
        request.state.user = None
    except Exception:
        logger.warning("access_token_decode_failed path=%s", request.url.path, exc_info=True)
        request.state.user = None


def _request_too_large(request: Request) -> bool:
    content_length = request.headers.get("content-length")
    if not content_length:
        return False
    try:
        return int(content_length) > Settings.max_request_bytes
    except ValueError:
        return False


def _request_too_large_response(request: Request):
    logger.warning("request_too_large path=%s", request.url.path)
    if _wants_json(request):
        return JSONResponse({"error": "request_too_large"}, status_code=413)
    return PlainTextResponse("Payload too large", status_code=413)


def _wants_json(request: Request) -> bool:
    accept = str(request.headers.get("accept") or "").lower()
    content_type = str(request.headers.get("content-type") or "").lower()
    return "application/json" in accept or "application/json" in content_type


def _is_cross_origin_write_request(request: Request) -> bool:
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return False
    source = _extract_request_origin(request)
    if not source:
        return False
    return source not in _get_allowed_origins(request)


def _extract_request_origin(request: Request) -> str | None:
    source = request.headers.get("Origin") or request.headers.get("Referer")
    if not source:
        return None
    parsed = urlparse(str(source).strip())
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def _normalize_origin(value: str | None) -> str | None:
    parsed = urlparse(str(value or "").strip())
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def _get_allowed_origins(request: Request) -> set[str]:
    host_url = f"{request.url.scheme}://{request.url.netloc}/"
    return {
        origin
        for origin in (
            _normalize_origin(host_url),
            _normalize_origin(Settings.app_base_url),
            *(_normalize_origin(item) for item in Settings.app_allowed_origins),
        )
        if origin
    }


def _is_static_request(request: Request) -> bool:
    return request.url.path.startswith("/static/")


def _is_scope_free_request(request: Request) -> bool:
    if _is_static_request(request):
        return True
    return request.url.path == "/watch/proxy"


def _build_request_container(root_container, *, request_state):
    if hasattr(root_container, "scope"):
        return root_container.scope(
            session_factory=get_session_factory(),
            request_state=request_state,
        )
    return root_container


def _apply_security_headers(response):
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "img-src 'self' data: https: blob:; "
        "style-src 'self' 'unsafe-inline' https:; "
        "style-src-elem 'self' 'unsafe-inline' https:; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "connect-src 'self' https:; "
        "media-src 'self' https: blob:; "
        "worker-src 'self' blob:; "
        "frame-src 'self' https:; "
        "font-src 'self' data: https:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'",
    )


def _clear_cookie(response, cookie_name: str):
    cookie_kwargs = {
        "httponly": True,
        "secure": Settings.cookie_secure,
        "samesite": Settings.cookie_samesite,
        "path": "/",
    }
    if Settings.cookie_domain:
        cookie_kwargs["domain"] = Settings.cookie_domain
    response.delete_cookie(cookie_name, **cookie_kwargs)
