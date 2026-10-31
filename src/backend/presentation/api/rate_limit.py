"""Декоратор ограничения частоты запросов для HTTP-роутов.

Соединяет порт :class:`RateLimiterInterface` с HTTP-ответами уровня
presentation. Формирование ответов и редиректов живёт здесь, поэтому
инфраструктура никогда не работает с HTTP-типами, а presentation не знает о
конкретном счётчике.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from http import HTTPStatus
from typing import Any

from fastapi import Request
from fastapi.responses import RedirectResponse

from backend.application.interface.services import RateLimiterInterface
from backend.presentation.api.errors import ErrorDetails, error_response
from backend.presentation.dependencies.client_ip import client_ip
from backend.presentation.dependencies.container import (
    ContainerUnavailableError,
    resolve,
)
from backend.presentation.web import flash

logger = logging.getLogger("anime_epic_moments")

RATE_LIMIT_UNAVAILABLE_STATUS = int(HTTPStatus.SERVICE_UNAVAILABLE)
RATE_LIMIT_EXCEEDED_STATUS = int(HTTPStatus.TOO_MANY_REQUESTS)


def rate_limit(
    scope: str,
    limit: int,
    window_seconds: int,
    key_builder: Callable[[Request], Awaitable[str]] | None = None,
    response_mode: str = "json",
    redirect_endpoint: str | None = None,
    message: str = "Слишком много запросов. Попробуйте позже.",
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Ограничить частоту вызовов асинхронного эндпоинта.

    Если лимитер не удалось получить из контейнера, запрос отклоняется с
    кодом 503: защита работает fail-closed и не пропускает трафик без
    учёта. Куки авторизации клиента при этом не используются.

    Args:
        scope: Область ограничения.
        limit: Максимум запросов в окне.
        window_seconds: Размер окна в секундах.
        key_builder: Асинхронная функция, возвращающая субъект ограничения.
            По умолчанию используется IP-адрес клиента.
        response_mode: ``json`` отвечает телом 429, ``redirect`` показывает
            flash-сообщение и возвращает на страницу.
        redirect_endpoint: Имя эндпоинта для режима ``redirect``.
        message: Текст flash-сообщения для режима ``redirect``.

    Returns:
        Callable: Декоратор, оборачивающий обработчик ограничением частоты.
    """

    def decorator(view: Callable[..., Awaitable[Any]]):
        """Обернуть обработчик проверкой частоты запросов.

        Args:
            view: Обработчик маршрута, который нужно ограничить.

        Returns:
            Callable: Обёрнутый обработчик с тем же именем и докстрингом.
        """

        @wraps(view)
        async def wrapped(*args: Any, **kwargs: Any):
            """Проверить лимит и вызвать обработчик либо вернуть отказ.

            Args:
                args: Позиционные аргументы обработчика.
                kwargs: Именованные аргументы обработчика.

            Returns:
                Any: Ответ обработчика или ответ отказа по лимиту.
            """
            request = _extract_request(args, kwargs)
            limiter = await _resolve_limiter(request)
            if limiter is None:
                logger.error(
                    "rate_limiter_unavailable scope=%s path=%s",
                    scope,
                    request.url.path,
                )
                return error_response(
                    "rate_limiter_unavailable",
                    "Ограничитель частоты запросов недоступен",
                    HTTPStatus(RATE_LIMIT_UNAVAILABLE_STATUS),
                )

            subject = await (key_builder(request) if key_builder else client_ip(request))
            decision = await limiter.hit(
                scope=scope,
                subject=subject,
                limit=limit,
                window_seconds=window_seconds,
            )
            if decision.allowed:
                return await view(*args, **kwargs)

            logger.warning(
                "rate_limit_exceeded scope=%s subject=%s retry_after=%s",
                scope,
                subject,
                decision.retry_after,
            )
            if response_mode == "redirect":
                await flash(request, message)
                return RedirectResponse(
                    url=_redirect_target(request, redirect_endpoint),
                    status_code=HTTPStatus.SEE_OTHER,
                )
            response = error_response(
                "rate_limit_exceeded",
                message,
                HTTPStatus(RATE_LIMIT_EXCEEDED_STATUS),
                details=ErrorDetails(retry_after=decision.retry_after),
            )
            response.headers["Retry-After"] = str(decision.retry_after)
            return response

        return wrapped

    return decorator


async def current_count(request: Request, scope: str, subject: str) -> int:
    """Прочитать текущее значение счётчика ограничения без увеличения.

    Args:
        request: Текущий HTTP-запрос.
        scope: Область ограничения.
        subject: Субъект ограничения.

    Returns:
        int: Число запросов в текущем окне; 0, если счётчик недоступен.
    """
    try:
        limiter = await _resolve_limiter(request)
        if limiter is None:
            return 0
        return await limiter.current(scope=scope, subject=subject)
    except ContainerUnavailableError:
        logger.exception("rate_limiter_unavailable path=%s", request.url.path)
        return 0


async def _resolve_limiter(request: Request) -> RateLimiterInterface | None:
    """Разрешить лимитер через единственную точку доступа к контейнеру.

    Обёртка :func:`backend.presentation.dependencies.container.resolve`
    используется вместо прямого ``container.get``: так у presentation остаётся
    ровно одно место, где он касается контейнера dishka, и обработчик отказа
    (``ContainerUnavailableError``) у всех потребителей одинаковый.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        RateLimiterInterface | None: Лимитер либо None, если контейнер недоступен.
    """
    try:
        return await resolve(request, RateLimiterInterface)
    except ContainerUnavailableError:
        logger.exception("rate_limiter_resolve_failed path=%s", request.url.path)
        return None


def _redirect_target(request: Request, redirect_endpoint: str | None) -> str:
    """Определить безопасный адрес возврата после отказа по лимиту.

    Заголовок ``Referer`` намеренно не используется: он контролируется
    клиентом и позволяет отправить пользователя на внешний домен.

    Args:
        request: Текущий HTTP-запрос.
        redirect_endpoint: Имя эндпоинта для возврата.

    Returns:
        str: Внутренний путь для редиректа.
    """
    if redirect_endpoint:
        return str(request.app.url_path_for(redirect_endpoint))
    return "/"


def _extract_request(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Request:
    """Извлечь объект Request из аргументов декорируемого обработчика.

    Args:
        args: Позиционные аргументы обработчика.
        kwargs: Именованные аргументы обработчика.

    Returns:
        Request: Извлечённый запрос.

    Raises:
        RuntimeError: Среди аргументов нет объекта Request.
    """
    if "request" in kwargs and isinstance(kwargs["request"], Request):
        return kwargs["request"]
    for value in args:
        if isinstance(value, Request):
            return value
    raise RuntimeError("rate_limit decorator requires a FastAPI Request argument")


__all__ = ["client_ip", "current_count", "rate_limit"]
