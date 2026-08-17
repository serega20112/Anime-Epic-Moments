"""HTTP request helpers for presentation layer."""

from __future__ import annotations

from typing import Any

from fastapi import Request


async def get_current_user(request: Request):
    """Return the current authenticated user.

    Args:
        request: Incoming HTTP request.

    Returns:
        object | None: Authenticated user or None.
    """
    return getattr(request.state, "user", None)


async def read_payload(request: Request) -> Any:
    """Read the request payload as JSON or form data.

    Args:
        request: Incoming HTTP request.

    Returns:
        Any: Parsed payload.
    """
    content_type = str(request.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        try:
            return await request.json()
        except Exception:
            return {}
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        return await request.form()
    try:
        return await request.json()
    except Exception:
        try:
            return await request.form()
        except Exception:
            return {}


async def wants_json(request: Request) -> bool:
    """Determine if the client expects a JSON response.

    Args:
        request: Incoming HTTP request.

    Returns:
        bool: True if client accepts application/json.
    """
    accept = str(request.headers.get("accept") or "").lower()
    content_type = str(request.headers.get("content-type") or "").lower()
    return "application/json" in accept or "application/json" in content_type
