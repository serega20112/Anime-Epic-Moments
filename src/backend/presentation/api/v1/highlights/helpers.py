"""Общие помощники маршрутов хайлайтов."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import Request
from fastapi.responses import RedirectResponse

MAX_LIMIT = 100


def read_limit(request: Request, *, default: int, maximum: int = MAX_LIMIT) -> int:
    """Прочитать и ограничить параметр ``limit`` из строки запроса.

    Args:
        request: Текущий HTTP-запрос.
        default: Значение по умолчанию, если параметра нет или он не число.
        maximum: Максимально допустимое значение.

    Returns:
        int: Ограниченное число записей.
    """
    raw = request.query_params.get("limit")
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return default
    return max(min(parsed, maximum), 1)


def redirect_login(request: Request) -> RedirectResponse:
    """Собрать редирект на страницу входа.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        RedirectResponse: Редирект 303 на страницу входа.
    """
    return RedirectResponse(
        url=request.app.url_path_for("auth.login_page"),
        status_code=HTTPStatus.SEE_OTHER,
    )
