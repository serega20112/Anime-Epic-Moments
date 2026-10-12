"""Rate-limit decorator for HTTP routes.

The decorator composes the infrastructure-level :class:`RateLimiter` with
presentation-level HTTP responses. Redirect/flash handling lives here so the
infrastructure layer never issues HTTP redirects.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse

from backend.infrastructure.web import flash

logger = logging.getLogger("anime_epic_moments")


def _extract_request(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Request:
    if "request" in kwargs and isinstance(kwargs["request"], Request):
        return kwargs["request"]
    for value in args:
        if isinstance(value, Request):
            return value
    raise RuntimeError("rate_limit decorator requires a FastAPI Request argument")


def rate_limit(
    scope: str,
    limit: int,
    window_seconds: int,
    key_builder: Callable[[Request], Awaitable[str]],
    response_mode: str = "json",
    redirect_endpoint: str | None = None,
    message: str = "Слишком много запросов. Попробуйте позже.",
):
    """Limit async endpoint calls using request-scoped container rate limiter.

    Args:
        scope: Rate-limit scope key.
        limit: Maximum number of requests per window.
        window_seconds: Window size in seconds.
        key_builder: Async callable producing the rate-limit subject.
        response_mode: "json" returns a 429 JSON, "redirect" flashes a message
            and redirects back.
        redirect_endpoint: Endpoint name used when response_mode is "redirect".
        message: Flash message used when response_mode is "redirect".
    """

    def decorator(view: Callable[..., Awaitable[Any]]):
        @wraps(view)
        async def wrapped(*args, **kwargs):
            request = _extract_request(args, kwargs)
            dishka_container = getattr(request.state, "dishka_container", None)
            if dishka_container is None:
                return await view(*args, **kwargs)

            from backend.infrastructure.security.rate_limiter import RateLimiter

            limiter = await dishka_container.get(RateLimiter)
            if limiter is None:
                return await view(*args, **kwargs)

            subject = await key_builder(request)
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


__all__ = ["rate_limit"]
