"""Общие схемы ответов-ошибок маршрутов коллекций мобильного клиента."""

from __future__ import annotations

from http import HTTPStatus

from backend.presentation.api.errors import ErrorResponse

OWNER_ERROR_RESPONSES = {
    HTTPStatus.UNAUTHORIZED: {"model": ErrorResponse},
    HTTPStatus.FORBIDDEN: {"model": ErrorResponse},
}
