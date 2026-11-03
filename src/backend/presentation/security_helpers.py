"""Помощники безопасности уровня запроса для middleware приложения."""

from __future__ import annotations

import logging
from http import HTTPStatus
from urllib.parse import urlparse

from fastapi import Request
from fastapi.responses import PlainTextResponse

from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.services import (
    CSRFServiceInterface,
    CSRFToken,
    JWTServiceInterface,
    TokenBlocklistInterface,
)
from backend.application.policies import CookiePolicy, RequestPolicy
from backend.domain.exceptions import InvalidTokenError
from backend.presentation.api.errors import (
    ERROR_REQUEST_TOO_LARGE,
    error_response,
    expects_json,
)
from backend.presentation.api.version import API_PREFIX
from backend.presentation.dependencies.container import (
    ContainerUnavailableError,
    resolve,
)
from backend.utils.logging import user_id_var

logger = logging.getLogger("anime_epic_moments")

BEARER_PREFIX = "bearer"
ACCESS_TOKEN_COOKIE = "access_token"
AUTH_TOKEN_SOURCE_STATE = "auth_token_source"
TOKEN_SOURCE_BEARER = "bearer"
TOKEN_SOURCE_COOKIE = "cookie"
STATIC_PATH_PREFIX = "/static/"
MEDIA_PROXY_PATH = "/watch/proxy"
API_AUTH_PREFIX = f"{API_PREFIX}/auth"
CSRF_EXEMPT_PATHS = frozenset({MEDIA_PROXY_PATH})


def extract_bearer_token(request: Request) -> str | None:
    """Вернуть токен из заголовка ``Authorization`` либо None.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        str | None: Значение Bearer-токена, если заголовок заявлен корректно.
    """
    header = str(request.headers.get("authorization") or "").strip()
    if not header.lower().startswith(f"{BEARER_PREFIX} "):
        return None
    return header[len(BEARER_PREFIX) :].strip() or None


def is_bearer_request(request: Request) -> bool:
    """Проверить, что запрос идёт от API-клиента с Bearer-токеном.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        bool: True, если заголовок ``Authorization`` содержит Bearer-токен.
    """
    return extract_bearer_token(request) is not None


def resolve_access_token(request: Request) -> tuple[str, str]:
    """Выбрать access-токен из заголовка или cookie — единственная точка разбора.

    Обе схемы аутентификации проходят через один код, чтобы проверка токена,
    список отозванных и отказ различались только источником значения.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        tuple[str, str]: Пара (значение токена, имя источника) либо пустая строка
            токена, если ни один источник не заполнен.
    """
    bearer_token = extract_bearer_token(request)
    if bearer_token is not None:
        return bearer_token, TOKEN_SOURCE_BEARER
    cookie_token = str(request.cookies.get(ACCESS_TOKEN_COOKIE) or "").strip()
    return cookie_token, TOKEN_SOURCE_COOKIE


async def load_user(request: Request):
    """Загрузить пользователя по access-токену и положить в состояние запроса.

    Токен берётся из заголовка ``Authorization: Bearer`` либо из cookie — обе
    схемы проходят через один код проверки и через один список отозванных.

    Args:
        request: Текущий HTTP-запрос.
    """
    token, token_source = resolve_access_token(request)
    setattr(request.state, AUTH_TOKEN_SOURCE_STATE, token_source)
    if not token:
        return

    try:
        token_blocklist = await resolve(request, TokenBlocklistInterface)
        if token_blocklist is not None and await token_blocklist.is_revoked(token):
            logger.info(
                "revoked_access_token_used path=%s source=%s", request.url.path, token_source
            )
            if token_source == TOKEN_SOURCE_COOKIE:
                request.state.clear_access_token_cookie = True
            return
        jwt_service = await resolve(request, JWTServiceInterface)
        user_id = await jwt_service.decode_token(token)
        user_repository = await resolve(request, UserRepository)
        user = await user_repository.get_by_id(user_id)
        if user is None:
            logger.info("access_token_user_missing user_id=%s", user_id)
            if token_source == TOKEN_SOURCE_COOKIE:
                request.state.clear_access_token_cookie = True
            return
        request.state.user = user
        user_id_var.set(str(user_id))
    except InvalidTokenError as error:
        logger.info(
            "access_token_rejected reason=%s path=%s",
            error.__class__.__name__,
            request.url.path,
        )
        if token_source == TOKEN_SOURCE_COOKIE:
            request.state.clear_access_token_cookie = True
        request.state.user = None
    except ContainerUnavailableError:
        logger.exception("security_dependencies_unavailable path=%s", request.url.path)
        request.state.auth_dependency_error = True
        request.state.user = None


async def request_too_large(request: Request) -> bool:
    """Проверить, превышает ли заявленный размер тела запроса предел."""
    content_length = request.headers.get("content-length")
    if not content_length:
        return False
    policy = await resolve(request, RequestPolicy)
    try:
        return int(content_length) > policy.max_request_bytes
    except ValueError:
        return False


async def request_too_large_response(request: Request):
    """Вернуть ответ 413 «тело запроса слишком велико»."""
    logger.warning("request_too_large path=%s", request.url.path)
    if expects_json(request):
        return error_response(
            ERROR_REQUEST_TOO_LARGE,
            "Тело запроса слишком велико",
            HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        )
    return PlainTextResponse(
        "Payload too large",
        status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
    )


async def is_cross_origin_write_request(request: Request) -> bool:
    """Проверить, что запрос на изменение пришёл с чужого источника."""
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return False
    source = await extract_request_origin(request)
    if not source:
        return False
    return source not in await get_allowed_origins(request)


async def extract_request_origin(request: Request) -> str | None:
    """Извлечь нормализованный источник запроса из заголовков."""
    source = request.headers.get("Origin") or request.headers.get("Referer")
    if not source:
        return None
    parsed = urlparse(str(source).strip())
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


async def normalize_origin(value: str | None) -> str | None:
    """Нормализовать строку источника запроса."""
    parsed = urlparse(str(value or "").strip())
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


async def get_allowed_origins(request: Request) -> set[str]:
    """Собрать белый список origin из конфигурации приложения.

    Заголовок ``Host`` намеренно не учитывается: он контролируется клиентом,
    и добавление производного origin превращало бы проверку в тавтологию.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        set[str]: Разрешённые origin.
    """
    policy = await resolve(request, RequestPolicy)
    candidates = {await normalize_origin(policy.base_url)}
    candidates.update(
        origin
        for origin in [await normalize_origin(item) for item in policy.allowed_origins]
        if origin
    )
    return candidates


async def is_static_request(request: Request) -> bool:
    """Проверить, что запрос адресован статическим файлам.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        bool: True для путей из хранилища статики.
    """
    return request.url.path.startswith(STATIC_PATH_PREFIX)


async def is_scope_free_request(request: Request) -> bool:
    """Проверить, что запросу не нужна область пользовательской сессии.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        bool: True для статики и проксируемого медиапотока.
    """
    if await is_static_request(request):
        return True
    return request.url.path == MEDIA_PROXY_PATH


async def is_csrf_exempt(request: Request) -> bool:
    """Проверить, что запрос освобождён от проверки CSRF.

    Освобождения три, и все они обоснованы письменно (задача S3.3):
    статика не меняет состояние; прокси медиапотока читает чужой HLS по
    разовому адресу и не трогает пользовательские данные; выпуск, продление и
    отзыв токенов работают без куки-сессии, а у Bearer-клиента токена CSRF ещё
    нет — защита от подделки запросов для них не имеет смысла.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        bool: True, если проверка CSRF не выполняется.
    """
    path = request.url.path
    return (
        path.startswith(STATIC_PATH_PREFIX)
        or path.startswith(API_AUTH_PREFIX)
        or path in CSRF_EXEMPT_PATHS
    )


async def prepare_csrf_token(request: Request) -> None:
    """Создать или достать из сессии CSRF-токен для запроса."""
    session = request.scope.get("session")
    if not isinstance(session, dict):
        return
    token = await session_csrf_token(request, session)
    if token is None:
        csrf_service = await resolve(request, CSRFServiceInterface)
        token = csrf_service.generate_token()
        session["csrf_token"] = token.to_session()
    request.state.csrf_token = token.value


async def validate_csrf(request: Request) -> bool:
    """Проверить CSRF-токен из заголовка или поля формы.

    Запросы с ``Authorization: Bearer`` освобождаются от проверки: такой токен
    хранится у мобильного клиента и не подставляется браузером автоматически,
    поэтому межсайтовая подделка запросов к ним неприменима.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        bool: True для Bearer-запроса либо при совпадении токена с токеном сессии.
    """
    if is_bearer_request(request):
        return True
    session = request.scope.get("session")
    session_token = await session_csrf_token(request, session)
    csrf_service = await resolve(request, CSRFServiceInterface)
    if header_token := request.headers.get("X-CSRF-Token"):
        return csrf_service.is_valid(session_token, header_token)
    await request.body()
    form = await request.form()
    form_token = form.get("csrf_token")
    return csrf_service.is_valid(session_token, form_token if isinstance(form_token, str) else None)


async def session_csrf_token(request: Request, session: object) -> CSRFToken | None:
    """Прочитать токен CSRF из сессии, удалив просроченный.

    Args:
        request: Текущий HTTP-запрос.
        session: Объект сессии запроса.

    Returns:
        CSRFToken | None: Действительный токен либо None.
    """
    if not isinstance(session, dict):
        return None
    token = CSRFToken.from_session(session.get("csrf_token"))
    if token is not None and token.is_expired():
        logger.info("csrf_token_expired path=%s", request.url.path)
        session.pop("csrf_token", None)
        return None
    return token


async def apply_security_headers(request: Request, response):
    """Проставить заголовки безопасности HTTP.

    Включает CSP, HSTS, `X-Frame-Options`, `X-Content-Type-Options`,
    `Referrer-Policy`.

    ``script-src`` не содержит ``'unsafe-eval'``: собственный JS приложения не
    использует ``eval`` и ``new Function``, а сторонние скрипты из сети не
    подключаются. ``'unsafe-inline'`` пока остаётся из-за одного inline-блока
    в ``highlight/list.html`` и атрибутов ``style=``; план перехода на nonce
    описан в ``docs/01-architecture/security.md``.

    Args:
        request: Текущий HTTP-запрос — нужен для политики HSTS.
        response: HTTP-ответ, которому добавляются заголовки.
    """
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    policy = await resolve(request, RequestPolicy)
    if policy.cookie_secure:
        response.headers.setdefault(
            "Strict-Transport-Security",
            f"max-age={policy.hsts_max_age}; includeSubDomains",
        )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "img-src 'self' data: https: blob:; "
        "style-src 'self' 'unsafe-inline' https:; "
        "style-src-elem 'self' 'unsafe-inline' https:; "
        "script-src 'self' 'unsafe-inline'; "
        "connect-src 'self' https:; "
        "media-src 'self' https: blob:; "
        "worker-src 'self' blob:; "
        "frame-src 'self' https:; "
        "font-src 'self' data: https:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'",
    )


async def clear_cookie(request: Request, response, cookie_name: str):
    """Удалить cookie по имени с корректными атрибутами безопасности.

    Args:
        request: Текущий HTTP-запрос — нужен для политики cookie.
        response: HTTP-ответ, из которого удаляется cookie.
        cookie_name: Имя удаляемого cookie.
    """
    policy = await resolve(request, CookiePolicy)
    cookie_kwargs = {
        "httponly": True,
        "secure": policy.secure,
        "samesite": policy.samesite,
        "path": "/",
    }
    if policy.domain:
        cookie_kwargs["domain"] = policy.domain
    response.delete_cookie(cookie_name, **cookie_kwargs)
