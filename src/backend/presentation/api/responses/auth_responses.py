"""Модели ответов маршрутов аутентификации."""

from __future__ import annotations

from pydantic import BaseModel

REFRESH_OK_STATUS = "ok"


class SessionRefreshResponse(BaseModel):
    """Ответ продления cookie-сессии браузера.

    Токены уходят в cookie, поэтому телу остаётся только подтвердить успех.

    Attributes:
        status: Метка ``ok`` — сессия продлена.
    """

    status: str = REFRESH_OK_STATUS
