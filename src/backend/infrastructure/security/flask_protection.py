from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import current_app, flash, jsonify, redirect, request, url_for


def client_ip() -> str:
    """Возвращает IP клиента с учетом X-Forwarded-For."""
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip() or "unknown"
    return (request.remote_addr or "unknown").strip()


def rate_limit(
    container_getter: Callable[[], object],
    scope: str,
    limit: int,
    window_seconds: int,
    key_builder: Callable[[], str] | None = None,
    response_mode: str = "json",
    redirect_endpoint: str | None = None,
    message: str = "Слишком много запросов. Попробуйте позже.",
):
    """Ограничивает частоту вызова Flask-endpoint через RateLimiter."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            container = container_getter()
            limiter = getattr(container, "rate_limiter", None)
            if limiter is None:
                return view(*args, **kwargs)

            subject = key_builder() if key_builder else client_ip()
            decision = limiter.hit(
                scope=scope,
                subject=subject,
                limit=limit,
                window_seconds=window_seconds,
            )
            if decision.allowed:
                return view(*args, **kwargs)

            current_app.logger.warning(
                "rate_limit_exceeded scope=%s subject=%s retry_after=%s",
                scope,
                subject,
                decision.retry_after,
            )
            if response_mode == "redirect":
                flash(message)
                if redirect_endpoint:
                    return redirect(url_for(redirect_endpoint)), 429
                return redirect(request.referrer or "/"), 429
            return (
                jsonify(
                    {
                        "error": "rate_limit_exceeded",
                        "retry_after": decision.retry_after,
                    }
                ),
                429,
            )

        return wrapped

    return decorator
