"""Общие элементы JSON-маршрутов аутентификации мобильного клиента."""

from __future__ import annotations

from fastapi import Request

from backend.presentation.api.errors import ErrorResponse
from backend.presentation.api.rate_limit import client_ip

ERROR_RESPONSES = {
    "401": {"model": ErrorResponse},
    "422": {"model": ErrorResponse},
    "429": {"model": ErrorResponse},
}


async def client_ip_key(request: Request) -> str:
    """Собрать субъект ограничения частоты по адресу клиента.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        str: IP-адрес клиента.
    """
    return await client_ip(request)
