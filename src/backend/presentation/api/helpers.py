"""Вспомогательные HTTP-функции слоя presentation.

Здесь только то, что нужно обслуживающему коду: кто текущий пользователь
запроса и ждёт ли клиент JSON. Разбором тела запросов занимаются схемы Pydantic
в маршрутах, поэтому угадывать формат содержимого здесь больше нечем.
Бизнес-правил тут нет и быть не должно.
"""

from __future__ import annotations

from fastapi import Request

JSON_CONTENT_TYPE = "application/json"


async def get_current_user(request: Request):
    """Вернуть аутентифицированного пользователя запроса.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        object | None: Пользователь сессии либо None для гостя.
    """
    return getattr(request.state, "user", None)


def wants_json(request: Request) -> bool:
    """Определить, ждёт ли клиент JSON-ответ.

    Используется обработчиками ошибок и middleware, чтобы для AJAX-клиента
    вернуть машиночитаемое тело, а для обычного браузера — HTML-страницу.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        bool: True, если клиент принимает application/json.
    """
    accept = str(request.headers.get("accept") or "").lower()
    content_type = str(request.headers.get("content-type") or "").lower()
    return JSON_CONTENT_TYPE in accept or JSON_CONTENT_TYPE in content_type
