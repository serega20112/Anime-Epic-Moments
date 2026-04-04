"""
Backward-compatible auth helpers for FastAPI handlers/tests.
"""

from __future__ import annotations

from functools import wraps

from fastapi import Request
from fastapi.responses import JSONResponse

from src.backend.infrastructure.security.jwt_service import JWTService
from src.backend.infrastructure.security.password_service import PasswordService

password_service = PasswordService()
jwt_service = JWTService()


def auth_required(handler):
    @wraps(handler)
    async def decorated(request: Request, *args, **kwargs):
        token = str(request.headers.get("Authorization") or "").strip()
        if not token:
            return JSONResponse({"error": "Authorization token required"}, status_code=401)
        try:
            user_id = jwt_service.decode_token(token)
        except Exception:
            return JSONResponse({"error": "Invalid or expired token"}, status_code=401)

        kwargs["user_id"] = user_id
        return await handler(request, *args, **kwargs)

    return decorated
