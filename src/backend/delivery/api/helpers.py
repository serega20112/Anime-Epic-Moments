from __future__ import annotations

from typing import Any

from fastapi import Request

from src.backend.dependencies.container import RequestContainer


def get_container(request: Request) -> RequestContainer:
    return request.state.container


def get_current_user(request: Request):
    return getattr(request.state, "user", None)


async def read_payload(request: Request) -> Any:
    content_type = str(request.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        try:
            return await request.json()
        except Exception:
            return {}
    if (
        "application/x-www-form-urlencoded" in content_type
        or "multipart/form-data" in content_type
    ):
        return await request.form()
    try:
        return await request.json()
    except Exception:
        try:
            return await request.form()
        except Exception:
            return {}


def wants_json(request: Request) -> bool:
    accept = str(request.headers.get("accept") or "").lower()
    content_type = str(request.headers.get("content-type") or "").lower()
    return "application/json" in accept or "application/json" in content_type
