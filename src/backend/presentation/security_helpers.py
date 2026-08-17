"""Request-scoped security helpers used by the application middleware.

These helpers are extracted from the app factory so the factory stays a thin
composition point and the request/CSRF/origin/size logic can be reasoned about
and tested in isolation.
"""

from __future__ import annotations

import logging
import secrets
from http import HTTPStatus
from urllib.parse import urlparse

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse

from backend.config import Settings
from backend.infrastructure.repositories.user_repository import UserRepository
from backend.infrastructure.security.csrf_service import csrf_service
from backend.infrastructure.security.jwt_service import JWTService
from backend.infrastructure.security.token_blocklist import TokenBlocklist
from backend.utils.logging import user_id_var

logger = logging.getLogger("anime_epic_moments")


async def load_user(request: Request):
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
        user_id = await jwt_service.decode_token(token)
        user_repository = await dishka_container.get(UserRepository)
        request.state.user = await user_repository.get_by_id(user_id)
        user_id_var.set(str(user_id))
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


async def request_too_large(request: Request) -> bool:
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


async def request_too_large_response(request: Request):
    """Return a 413 Payload Too Large response.

    Args:
        request: Current HTTP request.

    Returns:
        JSONResponse or PlainTextResponse: 413 error response.
    """
    logger.warning("request_too_large path=%s", request.url.path)
    if await wants_json(request):
        return JSONResponse(
            {"error": "request_too_large"},
            status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        )
    return PlainTextResponse(
        "Payload too large",
        status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
    )


async def wants_json(request: Request) -> bool:
    """Determine if the client expects a JSON response.

    Args:
        request: Current HTTP request.

    Returns:
        bool: True if client accepts application/json.
    """
    accept = str(request.headers.get("accept") or "").lower()
    content_type = str(request.headers.get("content-type") or "").lower()
    return "application/json" in accept or "application/json" in content_type


async def is_cross_origin_write_request(request: Request) -> bool:
    """Check if request is a cross-origin write operation.

    Args:
        request: Current HTTP request.

    Returns:
        bool: True if request origin is not in allowed list.
    """
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return False
    source = await extract_request_origin(request)
    if not source:
        return False
    return source not in await get_allowed_origins(request)


async def extract_request_origin(request: Request) -> str | None:
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


async def normalize_origin(value: str | None) -> str | None:
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


async def get_allowed_origins(request: Request) -> set[str]:
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
            await normalize_origin(host_url),
            await normalize_origin(Settings.app_base_url),
            *(await normalize_origin(item) for item in Settings.app_allowed_origins),
        )
        if origin
    }


async def is_static_request(request: Request) -> bool:
    """Check if request targets static files.

    Args:
        request: Current HTTP request.

    Returns:
        bool: True if path starts with /static/.
    """
    return request.url.path.startswith("/static/")


async def is_scope_free_request(request: Request) -> bool:
    """Check if request does not require user session scope.

    Args:
        request: Current HTTP request.

    Returns:
        bool: True for static files or watch proxy.
    """
    if await is_static_request(request):
        return True
    return request.url.path == "/watch/proxy"


async def is_csrf_exempt(request: Request) -> bool:
    """Check if request is exempt from CSRF validation.

    Auth routes are exempt because they are protected by Origin check.

    Args:
        request: Current HTTP request.

    Returns:
        bool: True if CSRF validation should be skipped.
    """
    path = request.url.path
    return any(path.startswith(prefix) for prefix in ("/auth", "/static", "/watch/proxy"))


async def prepare_csrf_token(request: Request) -> None:
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
    token = await csrf_service.generate_token(request.state)
    session["csrf_token"] = token


async def validate_csrf(request: Request) -> bool:
    """Validate a session CSRF token submitted via header or form field.

    JSON clients are protected by the Origin check in
    :func:`is_cross_origin_write_request` and only need a matching header token.
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
    if await wants_json(request):
        return True
    form = await request.form()
    form_token = form.get("csrf_token")
    if isinstance(form_token, str) and session_token:
        return secrets.compare_digest(form_token, session_token)
    return False


async def apply_security_headers(response):
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


async def clear_cookie(response, cookie_name: str):
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
