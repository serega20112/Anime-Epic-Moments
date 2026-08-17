"""Shared helpers for the highlight route modules."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import Request
from fastapi.responses import RedirectResponse


async def read_limit(request: Request, *, default: int, maximum: int) -> int:
    """Parse and clamp a limit query parameter.

    Args:
        request: Incoming HTTP request.
        default: Default value when missing or invalid.
        maximum: Maximum allowed value.

    Returns:
        int: Clamped limit.
    """
    raw = request.query_params.get("limit")
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return default
    return max(min(parsed, maximum), 1)


async def redirect_login(request: Request) -> RedirectResponse:
    """Build a redirect to the login page.

    Args:
        request: Incoming HTTP request.

    Returns:
        RedirectResponse: SEE_OTHER redirect to login.
    """
    return RedirectResponse(
        url=request.app.url_path_for("auth.login_page"),
        status_code=HTTPStatus.SEE_OTHER,
    )
