from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse

from backend.infrastructure.security.rate_limiter import RateLimiter
from backend.infrastructure.web import flash

logger = logging.getLogger("anime_epic_moments")


async def client_ip(request: Request) -> str:
    """Return client IP taking X-Forwarded-For into account."""
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host.strip()
    return "unknown"


def rate_limit(
    scope: str,
    limit: int,
    window_seconds: int,
    key_builder: Callable[[Request], Awaitable[str]] | None = None,
    response_mode: str = "json",
    redirect_endpoint: str | None = None,
    message: str = "Слишком много запросов. Попробуйте позже.",
):
    """Limit async endpoint calls using request-scoped container rate limiter."""

    def decorator(view: Callable[..., Awaitable[Any]]):
        @wraps(view)
        async def wrapped(*args, **kwargs):
            request = _extract_request(args, kwargs)
            dishka_container = getattr(request.state, "dishka_container", None)
            if dishka_container is not None:
                limiter = await dishka_container.get(RateLimiter)
            else:
                limiter = getattr(request.state, "container", None)
                limiter = getattr(limiter, "rate_limiter", None)
            if limiter is None:
                return await view(*args, **kwargs)

            subject = await (key_builder(request) if key_builder else client_ip(request))
            decision = await limiter.hit(
                scope=scope,
                subject=subject,
                limit=limit,
                window_seconds=window_seconds,
            )
            if decision.allowed:
                return await view(*args, **kwargs)

            logger.warning(
                "rate_limit_exceeded scope=%s subject=%s retry_after=%s",
                scope,
                subject,
                decision.retry_after,
            )
            if response_mode == "redirect":
                await flash(request, message)
                target = (
                    str(request.app.url_path_for(redirect_endpoint))
                    if redirect_endpoint
                    else request.headers.get("referer") or "/"
                )
                return RedirectResponse(url=target, status_code=303)
            return JSONResponse(
                {
                    "error": "rate_limit_exceeded",
                    "retry_after": decision.retry_after,
                },
                status_code=429,
            )

        return wrapped

    return decorator


def _extract_request(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Request:
    if "request" in kwargs and isinstance(kwargs["request"], Request):
        return kwargs["request"]
    for value in args:
        if isinstance(value, Request):
            return value
    raise RuntimeError("rate_limit decorator requires a FastAPI Request argument")
