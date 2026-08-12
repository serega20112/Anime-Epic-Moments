"""Flask application factory with middleware, security headers, and CSRF protection."""

from __future__ import annotations

import logging
import secrets
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

import jwt
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.config import Settings
from backend.events.lifecycle import register_lifecycle_handlers
from backend.infrastructure.di.providers import AppProvider, RequestProvider, UseCaseProvider
from backend.infrastructure.repositories.user_repository import UserRepository
from backend.infrastructure.security.csrf_service import csrf_service
from backend.infrastructure.security.jwt_service import JWTService
from backend.infrastructure.security.token_blocklist import TokenBlocklist
from backend.infrastructure.web import render_template
from backend.presentation.api.v1.anime_route import anime_router
from backend.presentation.api.v1.auth_route import auth_router
from backend.presentation.api.v1.collection_route import collection_router
from backend.presentation.api.v1.favorite_route import favorite_router
from backend.presentation.api.v1.highlight_route import highlight_router
from backend.presentation.api.v1.index_route import index_router
from backend.presentation.api.v1.recommendation_route import recommendation_router
from backend.presentation.api.v1.support_route import support_router
from backend.presentation.api.v1.user_route import user_router
from backend.presentation.api.v1.watch_route import (
    watch_router,
)

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
    app = FastAPI(debug=Settings.flask_debug)
    dishka_container = make_async_container(
        AppProvider(),
        RequestProvider(),
        UseCaseProvider(),
    )
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

    register_lifecycle_handlers(app)

    @app.middleware("http")
    async def app_context_middleware(request: Request, call_next):
        """Process each HTTP request through middleware pipeline.

        Validates request size, sets up DI container, loads user,
        generates CSRF token, validates CSRF for mutations.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.

        Returns:
            Response: HTTP response.
        """
        if _request_too_large(request):
            return _request_too_large_response(request)

        request.state.db_session = None
        request.state.user = None
        request.state.clear_access_token_cookie = False
        request.state.csrf_token = None

        if _is_cross_origin_write_request(request):
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
            if not _is_scope_free_request(request):
                await _load_user(request)
                _prepare_csrf_token(request)
            if request.method in {"POST", "PUT", "PATCH", "DELETE"} and not _is_csrf_exempt(
                    request
            ):
                if not await _validate_csrf(request):
                    logger.warning("csrf_validation_failed path=%s", request.url.path)
                    if _wants_json(request):
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
            _clear_cookie(response, "access_token")
        _apply_security_headers(response)
        return response

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

    @app.exception_handler(404)
    async def handle_not_found(request: Request, _error):
        """Handle 404 errors with a controlled response."""
        logger.warning("not_found path=%s", request.url.path)
        if _wants_json(request):
            return JSONResponse(
                {"error": "not_found"},
                status_code=HTTPStatus.NOT_FOUND,
            )
        return render_template(
            request,
            "errors/404.html",
            status_code=HTTPStatus.NOT_FOUND,
        )

    @app.exception_handler(Exception)
    async def handle_internal_error(request: Request, _error: Exception):
        """Handle unhandled exceptions with a controlled 500 response."""
        logger.exception("internal_server_error path=%s", request.url.path)
        if _wants_json(request):
            return JSONResponse(
                {"error": "internal_server_error"},
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        return render_template(
            request,
            "errors/500_modal.html",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    setup_dishka(container=dishka_container, app=app)

    return app


async def _load_user(request: Request):
    """Load user from access token cookie and attach to request state.

    Args:
        request: Current HTTP request.
    """
    token = request.cookies.get("access_token")
    if not token:
        return

    try:
        dishka_container = request.state.dishka_container
        token_blocklist = await dishka_container.get(TokenBlocklist)
        if token_blocklist is not None and await token_blocklist.is_revoked(token):
            logger.info("revoked_access_token_used path=%s", request.url.path)
            request.state.clear_access_token_cookie = True
            return
        jwt_service = await dishka_container.get(JWTService)
        user_id = jwt_service.decode_token(token)
        user_repository = await dishka_container.get(UserRepository)
        request.state.user = await user_repository.get_by_id(user_id)
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
    """Check if the request payload exceeds the maximum allowed size.

    Args:
        request: Current HTTP request.

    Returns:
        bool: True if payload exceeds max_request_bytes.
    """
    content_length = request.headers.get("content-length")
    if not content_length:
        return False
    try:
        return int(content_length) > Settings.max_request_bytes
    except ValueError:
        return False


def _request_too_large_response(request: Request):
    """Return a 413 Payload Too Large response.

    Args:
        request: Current HTTP request.

    Returns:
        JSONResponse or PlainTextResponse: 413 error response.
    """
    logger.warning("request_too_large path=%s", request.url.path)
    if _wants_json(request):
        return JSONResponse(
            {"error": "request_too_large"},
            status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        )
    return PlainTextResponse(
        "Payload too large",
        status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
    )


def _wants_json(request: Request) -> bool:
    """Determine if the client expects a JSON response.

    Args:
        request: Current HTTP request.

    Returns:
        bool: True if client accepts application/json.
    """
    accept = str(request.headers.get("accept") or "").lower()
    content_type = str(request.headers.get("content-type") or "").lower()
    return "application/json" in accept or "application/json" in content_type


def _is_cross_origin_write_request(request: Request) -> bool:
    """Check if request is a cross-origin write operation.

    Args:
        request: Current HTTP request.

    Returns:
        bool: True if request origin is not in allowed list.
    """
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return False
    source = _extract_request_origin(request)
    if not source:
        return False
    return source not in _get_allowed_origins(request)


def _extract_request_origin(request: Request) -> str | None:
    """Extract normalized origin URL from request headers.

    Args:
        request: Current HTTP request.

    Returns:
        str | None: Normalized origin or None if not found.
    """
    source = request.headers.get("Origin") or request.headers.get("Referer")
    if not source:
        return None
    parsed = urlparse(str(source).strip())
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def _normalize_origin(value: str | None) -> str | None:
    """Normalize an origin URL string.

    Args:
        value: Raw origin URL.

    Returns:
        str | None: Normalized origin or None.
    """
    parsed = urlparse(str(value or "").strip())
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def _get_allowed_origins(request: Request) -> set[str]:
    """Build set of allowed origins from settings and request context.

    Args:
        request: Current HTTP request.

    Returns:
        set[str]: Allowed origin URLs.
    """
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
    """Check if request targets static files.

    Args:
        request: Current HTTP request.

    Returns:
        bool: True if path starts with /static/.
    """
    return request.url.path.startswith("/static/")


def _is_scope_free_request(request: Request) -> bool:
    """Check if request does not require user session scope.

    Args:
        request: Current HTTP request.

    Returns:
        bool: True for static files or watch proxy.
    """
    if _is_static_request(request):
        return True
    return request.url.path == "/watch/proxy"


def _is_csrf_exempt(request: Request) -> bool:
    """Check if request is exempt from CSRF validation.

    Auth routes are exempt because they are protected by Origin check.

    Args:
        request: Current HTTP request.

    Returns:
        bool: True if CSRF validation should be skipped.
    """
    path = request.url.path
    return any(path.startswith(prefix) for prefix in ("/auth", "/static", "/watch/proxy"))


def _prepare_csrf_token(request: Request) -> None:
    """Create or load a session-persisted CSRF token for the request.

    Stores the token in the session so the value rendered into a form during
    a GET matches the one validated on a subsequent POST.

    Args:
        request: Current HTTP request.
    """
    session = request.scope.get("session")
    if not isinstance(session, dict):
        return
    stored = session.get("csrf_token")
    if isinstance(stored, str):
        request.state.csrf_token = stored
        return
    token = csrf_service.generate_token(request.state)
    session["csrf_token"] = token


async def _validate_csrf(request: Request) -> bool:
    """Validate a session CSRF token submitted via header or form field.

    JSON clients are protected by the Origin check in
    _is_cross_origin_write_request and only need a matching header token.
    Form submissions must include the csrf_token field rendered by the template.

    Args:
        request: Current HTTP request.

    Returns:
        bool: True if CSRF validation passes.
    """
    session = request.scope.get("session")
    session_token = session.get("csrf_token") if isinstance(session, dict) else None
    if header_token := request.headers.get("X-CSRF-Token"):
        return bool(session_token) and secrets.compare_digest(header_token, session_token)
    if _wants_json(request):
        return True
    form = await request.form()
    form_token = form.get("csrf_token")
    if isinstance(form_token, str) and session_token:
        return secrets.compare_digest(form_token, session_token)
    return False


def _apply_security_headers(response):
    """Apply security-related HTTP headers to the response.

    Includes CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy.

    Args:
        response: HTTP response to add headers to.
    """
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    if Settings.cookie_secure:
        response.headers.setdefault(
            "Strict-Transport-Security",
            f"max-age={Settings.hsts_max_age}; includeSubDomains",
        )
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
    """Delete a cookie by name with proper security attributes.

    Args:
        response: HTTP response to delete cookie from.
        cookie_name: Name of the cookie to clear.
    """
    cookie_kwargs = {
        "httponly": True,
        "secure": Settings.cookie_secure,
        "samesite": Settings.cookie_samesite,
        "path": "/",
    }
    if Settings.cookie_domain:
        cookie_kwargs["domain"] = Settings.cookie_domain
    response.delete_cookie(cookie_name, **cookie_kwargs)
