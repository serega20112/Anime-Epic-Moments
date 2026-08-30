"""Guard helpers for external HTTP responses.

Некоторые внешние эндпоинты (или захваченные домены) могут отвечать
редиректом на гигабайтные файлы: без проверки Content-Length клиент
скачивает тело целиком в память и блокирует запрос пользователя.
Здесь собрана единая проверка размера JSON-ответа перед чтением тела.
"""

from __future__ import annotations

from typing import Any

from backend.infrastructure.external.errors import ExternalServiceInvalidResponseError

MAX_JSON_BODY_BYTES = 10 * 1024 * 1024


def read_json_limited(response: Any, *, service_name: str) -> Any:
    """Читает JSON-тело ответа, отклоняя слишком большие payload.

    Args:
        response: Ответ httpx (уже выполненный запрос).
        service_name: Имя внешнего сервиса для ошибки.

    Returns:
        Any: Разобранный JSON.

    Raises:
        ExternalServiceInvalidResponseError: Объявленный размер тела превышает
            :data:`MAX_JSON_BODY_BYTES`.
    """
    content_length = str(response.headers.get("content-length") or "")
    if content_length.isdigit() and int(content_length) > MAX_JSON_BODY_BYTES:
        raise ExternalServiceInvalidResponseError(service_name=service_name)
    return response.json()
