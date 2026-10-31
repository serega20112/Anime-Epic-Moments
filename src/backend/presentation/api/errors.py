"""Единый контракт ошибок HTTP-слоя.

Все отказы JSON-клиентов описываются одной формой ``{code, message, details}``,
а код ответа берётся из :data:`ERROR_STATUS` — единственного места, где
исключение превращается в HTTP-статус. Обработчики регистрируются один раз в
:func:`register_exception_handlers`, поэтому маршруты не собирают тела ошибок
вручную и не дублируют таблицу статусов.
"""

from __future__ import annotations

import logging
import re
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel

from backend.application.interface.services import ImageStorageError
from backend.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DomainError,
    DuplicateError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from backend.presentation.api.helpers import wants_json
from backend.presentation.web import render_template

logger = logging.getLogger("anime_epic_moments")

ERROR_BAD_REQUEST = "bad_request"
ERROR_VALIDATION_FAILED = "validation_failed"
ERROR_UNAUTHORIZED = "unauthorized"
ERROR_FORBIDDEN = "forbidden"
ERROR_NOT_FOUND = "not_found"
ERROR_CONFLICT = "conflict"
ERROR_REQUEST_TOO_LARGE = "request_too_large"
ERROR_INTERNAL = "internal_server_error"
ERROR_EXTERNAL_SERVICE = "external_service_error"

JSON_API_PATH_PREFIX = "/api/"

ERROR_STATUS: dict[type[BaseException], HTTPStatus] = {
    RequestValidationError: HTTPStatus.UNPROCESSABLE_ENTITY,
    ValidationError: HTTPStatus.BAD_REQUEST,
    NotFoundError: HTTPStatus.NOT_FOUND,
    AuthenticationError: HTTPStatus.UNAUTHORIZED,
    AuthorizationError: HTTPStatus.FORBIDDEN,
    DuplicateError: HTTPStatus.CONFLICT,
    ExternalServiceError: HTTPStatus.BAD_GATEWAY,
    ImageStorageError: HTTPStatus.BAD_REQUEST,
    PermissionError: HTTPStatus.FORBIDDEN,
    ValueError: HTTPStatus.BAD_REQUEST,
    DomainError: HTTPStatus.BAD_REQUEST,
}

ERROR_CODES: dict[type[BaseException], str] = {
    ValidationError: ERROR_VALIDATION_FAILED,
    ImageStorageError: ERROR_VALIDATION_FAILED,
    NotFoundError: ERROR_NOT_FOUND,
    AuthenticationError: ERROR_UNAUTHORIZED,
    AuthorizationError: ERROR_FORBIDDEN,
    PermissionError: ERROR_FORBIDDEN,
    DuplicateError: ERROR_CONFLICT,
    ExternalServiceError: ERROR_EXTERNAL_SERVICE,
}

STATUS_CODES: dict[HTTPStatus, str] = {
    HTTPStatus.BAD_REQUEST: ERROR_BAD_REQUEST,
    HTTPStatus.UNAUTHORIZED: ERROR_UNAUTHORIZED,
    HTTPStatus.FORBIDDEN: ERROR_FORBIDDEN,
    HTTPStatus.NOT_FOUND: ERROR_NOT_FOUND,
    HTTPStatus.CONFLICT: ERROR_CONFLICT,
    HTTPStatus.UNPROCESSABLE_ENTITY: ERROR_VALIDATION_FAILED,
    HTTPStatus.BAD_GATEWAY: ERROR_EXTERNAL_SERVICE,
    HTTPStatus.SERVICE_UNAVAILABLE: ERROR_EXTERNAL_SERVICE,
    HTTPStatus.INTERNAL_SERVER_ERROR: ERROR_INTERNAL,
}

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


class ErrorFieldDetail(BaseModel):
    """Описание одного проблемного поля запроса.

    Attributes:
        location: Путь к полю в запросе, например ``body.email``.
        message: Текст требования, которое поле не выполнило.
    """

    location: str
    message: str


class ErrorDetails(BaseModel):
    """Структурные сведения об отказе, которые читает клиент.

    Поля намеренно перечислены, а не оставлены свободным словарём: мобильный
    клиент генерирует модели из OpenAPI, и свободный словарь лишает его типов.

    Attributes:
        fields: Перечень проблемных полей запроса.
        retry_after: Через сколько секунд разрешено повторить запрос.
    """

    fields: list[ErrorFieldDetail] = []
    retry_after: int | None = None


class ErrorResponse(BaseModel):
    """Тело отказа JSON API.

    Attributes:
        code: Машиночитаемый код ошибки, стабильный для клиентов.
        message: Текст для человека, обычно из исключения.
        details: Дополнительные сведения: поля формы, секунды до повтора.
    """

    code: str
    message: str
    details: ErrorDetails | None = None


def _resolve(error: BaseException, mapping: dict, default):
    """Найти первое совпадение по иерархии класса исключения.

    Args:
        error: Исключение, которое нужно описать.
        mapping: Таблица соответствий по типам исключений.
        default: Значение, если ни один тип из иерархии не описан.

    Returns:
        object: Значение из таблицы либо ``default``.
    """
    for error_class in type(error).__mro__:
        value = mapping.get(error_class)
        if value is not None:
            return value
    return default


def resolve_status(error: BaseException) -> HTTPStatus:
    """Определить HTTP-статус отказа по типу исключения.

    Args:
        error: Исключение, которое нужно превратить в статус.

    Returns:
        HTTPStatus: Статус из :data:`ERROR_STATUS` либо 500.
    """
    return _resolve(error, ERROR_STATUS, HTTPStatus.INTERNAL_SERVER_ERROR)


def resolve_code(error: BaseException) -> str:
    """Определить машиночитаемый код отказа.

    Код берётся из :data:`ERROR_CODES`, а для незнакомых исключений выводится
    из имени класса в ``snake_case`` — так новый доменный класс ошибки сразу
    получает осмысленный код без правки таблицы.

    Args:
        error: Исключение, которое нужно закодировать.

    Returns:
        str: Код ошибки для поля ``code``.
    """
    explicit = _resolve(error, ERROR_CODES, None)
    if explicit is not None:
        return str(explicit)
    raw_name = _CAMEL_BOUNDARY.sub("_", type(error).__name__).lower()
    return raw_name[: -len("_error")] if raw_name.endswith("_error") else raw_name


def error_payload(
    error: BaseException,
    *,
    code: str | None = None,
    message: str | None = None,
    details: ErrorDetails | None = None,
) -> ErrorResponse:
    """Собрать тело отказа в едином формате.

    Args:
        error: Исключение, которое описывается.
        code: Код ошибки, если он отличается от вычисленного по типу.
        message: Текст ошибки, если нужно заменить текст исключения.
        details: Дополнительные сведения для клиента.

    Returns:
        ErrorResponse: Готовое тело ответа.
    """
    return ErrorResponse(
        code=code or resolve_code(error),
        message=message or str(error) or resolve_code(error),
        details=details,
    )


def error_response(
    code: str,
    message: str,
    status: HTTPStatus,
    details: ErrorDetails | None = None,
) -> JSONResponse:
    """Собрать ответ отказа без исключения.

    Нужен там, где отказ — это результат проверки в маршруте, а не выброшенное
    исключение: гость без сессии, неверные поля формы.

    Args:
        code: Машиночитаемый код ошибки.
        message: Текст ошибки для человека.
        status: HTTP-статус ответа.
        details: Дополнительные сведения для клиента.

    Returns:
        JSONResponse: Ответ с телом :class:`ErrorResponse`.
    """
    payload = ErrorResponse(code=code, message=message, details=details)
    return JSONResponse(payload.model_dump(exclude_none=True), status_code=status)


def unauthorized_error(message: str = "Требуется вход в аккаунт") -> JSONResponse:
    """Ответить отказом гостю.

    Args:
        message: Текст ошибки для человека.

    Returns:
        JSONResponse: Ответ 401 с кодом ``unauthorized``.
    """
    return error_response(ERROR_UNAUTHORIZED, message, HTTPStatus.UNAUTHORIZED)


def expects_json(request: Request) -> bool:
    """Определить, что клиент ждёт машиночитаемый ответ.

    Пути JSON API отдают единое тело ошибки независимо от заголовка Accept:
    мобильный клиент часто шлёт ``*/*``, а HTML-заглушка ему бесполезна.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        bool: True для путей из ``/api/`` и для клиентов с Accept на JSON.
    """
    return str(request.url.path).startswith(JSON_API_PATH_PREFIX) or wants_json(request)


def code_for_status(status: HTTPStatus) -> str:
    """Подобрать код ошибки по HTTP-статусу.

    Используется там, где сценарий вернул только статус отказа и текст, а
    машиночитаемого кода нет.

    Args:
        status: HTTP-статус отказа.

    Returns:
        str: Код ошибки для поля ``code``.
    """
    return STATUS_CODES.get(status, ERROR_BAD_REQUEST)


def error_from_result(result: object) -> JSONResponse:
    """Собрать ответ отказа из результата сценария.

    Сценарии части подсистем возвращают объект с полями ``status_code`` и
    ``error``. Маршрут не разворачивает эти поля вручную, чтобы форма тела
    ошибки оставалась одинаковой во всех эндпоинтах.

    Args:
        result: Результат сценария с полями ``status_code`` и ``error``.

    Returns:
        JSONResponse: Ответ с единым телом ошибки.
    """
    status = HTTPStatus(int(getattr(result, "status_code", HTTPStatus.BAD_REQUEST)))
    message = str(getattr(result, "error", "") or code_for_status(status))
    return error_response(code_for_status(status), message, status)


async def json_error(
    request: Request,
    error: BaseException,
    *,
    status: HTTPStatus | None = None,
    code: str | None = None,
    message: str | None = None,
    details: ErrorDetails | None = None,
) -> Response:
    """Ответить клиенту единым телом ошибки.

    Args:
        request: Текущий HTTP-запрос.
        error: Исключение, которое описывается.
        status: Статус ответа; по умолчанию вычисляется по типу исключения.
        code: Код ошибки, если он отличается от вычисленного.
        message: Текст ошибки, если нужно заменить текст исключения.
        details: Дополнительные сведения для клиента.

    Returns:
        Response: JSON с телом :class:`ErrorResponse`.
    """
    resolved = status or resolve_status(error)
    payload = error_payload(error, code=code, message=message, details=details)
    return JSONResponse(
        payload.model_dump(exclude_none=True),
        status_code=resolved,
    )


async def handle_domain_error(request: Request, error: Exception) -> Response:
    """Обработать доменное исключение.

    JSON-клиенты получают единое тело ошибки, HTML-страницы — шаблон модального
    окна с тем же статусом, чтобы отказ не превращался в 500.

    Args:
        request: Текущий HTTP-запрос.
        error: Доменное исключение маршрута.

    Returns:
        Response: JSON или отрисованный шаблон ошибки.
    """
    status = resolve_status(error)
    log = logger.error if status >= HTTPStatus.INTERNAL_SERVER_ERROR else logger.warning
    log(
        "request_failed path=%s code=%s status=%s",
        request.url.path,
        resolve_code(error),
        int(status),
    )
    if expects_json(request):
        return await json_error(request, error, status=status)
    return await render_template(
        request,
        "errors/500_modal.html",
        status_code=status,
        error_message=str(error),
    )


async def handle_validation_error(request: Request, error: Exception) -> Response:
    """Обработать отказ валидации тела или параметров запроса.

    Args:
        request: Текущий HTTP-запрос.
        error: Ошибка разбора запроса.

    Returns:
        Response: JSON с перечнем проблемных полей.
    """
    details = ErrorDetails(
        fields=(
            [
                ErrorFieldDetail(
                    location=".".join(str(part) for part in item.get("loc", ())),
                    message=str(item.get("msg", "")),
                )
                for item in error.errors()
            ]
            if isinstance(error, RequestValidationError)
            else []
        )
    )
    logger.warning("request_invalid path=%s fields=%s", request.url.path, len(details.fields))
    return await json_error(
        request,
        error,
        status=HTTPStatus.UNPROCESSABLE_ENTITY,
        code=ERROR_VALIDATION_FAILED,
        message="Некорректные данные запроса",
        details=details,
    )


async def handle_not_found(request: Request, error: Exception) -> Response:
    """Обработать несуществующий маршрут или ресурс.

    Args:
        request: Текущий HTTP-запрос.
        error: Исключение маршрутизации.

    Returns:
        Response: JSON для API-клиентов или страница 404.
    """
    logger.warning("not_found path=%s", request.url.path)
    if expects_json(request):
        return await json_error(request, error, status=HTTPStatus.NOT_FOUND, code=ERROR_NOT_FOUND)
    return await render_template(request, "errors/404.html", status_code=HTTPStatus.NOT_FOUND)


async def handle_internal_error(request: Request, error: Exception) -> Response:
    """Обработать непредвиденное исключение.

    Args:
        request: Текущий HTTP-запрос.
        error: Исключение, которое не описал ни один обработчик.

    Returns:
        Response: JSON для API-клиентов или модальное окно ошибки.
    """
    logger.exception("internal_server_error path=%s", request.url.path)
    if expects_json(request):
        return await json_error(
            request,
            error,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            code=ERROR_INTERNAL,
            message="Внутренняя ошибка сервера",
        )
    return await render_template(
        request,
        "errors/500_modal.html",
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
    )


def declare_error_responses(app: FastAPI) -> None:
    """Заявить единое тело отказа валидации для всех маршрутов со входом.

    FastAPI по умолчанию подписывает 422 как ``HTTPValidationError`` с телом
    ``{"detail": [...]}``, но отвечает-то он через :func:`handle_validation_error`
    в форме ``{code, message, details}``. Без этой правки документированный
    контракт расходился бы с фактическим ответом, а клиент, построенный по
    OpenAPI, не смог бы разобрать отказ.

    Args:
        app: Приложение, маршрутам которого подывается схема отказа.
    """
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if (
            route.body_field is not None
            or route.dependant.path_params
            or route.dependant.query_params
        ):
            route.responses["422"] = {"model": ErrorResponse}


def register_exception_handlers(app: FastAPI) -> None:
    """Подключить обработчики ошибок и схему отказа 422 к приложению.

    Регистрирует единый контракт для доменных ошибок, отказов валидации,
    отсутствующих маршрутов и непредвиденных исключений, а также подменяет
    описание 422 у маршрутов с проверяемым входом. Вызывается один раз при
    сборке приложения, чтобы статусы и форма ответа были одинаковыми во всех
    маршрутах.

    Args:
        app: Приложение FastAPI, которому нужны обработчики.
    """
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(DomainError, handle_domain_error)
    app.add_exception_handler(404, handle_not_found)
    app.add_exception_handler(Exception, handle_internal_error)
    declare_error_responses(app)
