"""Помощники HTTP-ответов для маршрутов аутентификации.

Здесь результаты сценариев :class:`AuthResult` превращаются в редиректы,
cookie и flash-сообщения. Благодаря этому обработчики маршрутов остаются
тонкими и не содержат логики разбора исходов.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import RedirectResponse

from backend.application.interface.services import JWTServiceInterface
from backend.application.policies import CookiePolicy
from backend.application.use_cases.auth.result import AuthResult
from backend.presentation.dependencies.container import resolve as resolve_dependency
from backend.presentation.web import flash

SEE_OTHER = HTTPStatus.SEE_OTHER
ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"


@dataclass(frozen=True, slots=True)
class IssuedTokens:
    """Пара токенов пользователя с временем жизни каждого.

    Attributes:
        access_token: Коротко живущий токен доступа.
        refresh_token: Длительно живущий токен продления.
        access_expires_in: Время жизни access-токена в секундах.
        refresh_expires_in: Время жизни refresh-токена в секундах.
    """

    access_token: str
    refresh_token: str
    access_expires_in: int
    refresh_expires_in: int


async def mint_tokens(request: Request, user_id: int) -> IssuedTokens:
    """Создать новую пару токенов для пользователя.

    Единая точка выпуска токенов: cookie- сессия браузера и Bearer-сессия
    мобильного клиента получают одинаковые значения и одинаковые сроки.

    Args:
        request: Текущий HTTP-запрос — нужен для сервиса токенов и политики cookie.
        user_id: Идентификатор аутентифицированного пользователя.

    Returns:
        IssuedTokens: Свежая пара токенов и время их жизни.
    """
    jwt_service = await resolve_dependency(request, JWTServiceInterface)
    policy = await resolve_dependency(request, CookiePolicy)
    return IssuedTokens(
        access_token=await jwt_service.create_access_token(user_id),
        refresh_token=await jwt_service.create_refresh_token(user_id),
        access_expires_in=policy.access_max_age_seconds,
        refresh_expires_in=policy.refresh_max_age_seconds,
    )


async def resolve(request: Request, result: AuthResult) -> RedirectResponse:
    """Оформить редирект по результату без выдачи токенов.

    Args:
        request: Текущий HTTP-запрос.
        result: Результат сценария.

    Returns:
        RedirectResponse: Редирект на страницу успеха или ошибки.
    """
    if result.ok:
        if result.message:
            await flash(request, result.message)
        return await redirect(request, result.redirect_endpoint or "index.index")
    await flash(request, result.error_message or "")
    return await redirect(request, result.error_endpoint or "auth.login_page")


async def resolve_auth(request: Request, result: AuthResult) -> RedirectResponse:
    """Оформить редирект по результату входа и выдать cookie токенов.

    Args:
        request: Текущий HTTP-запрос.
        result: Результат сценария входа или регистрации.

    Returns:
        RedirectResponse: Редирект; при успехе — с установленными cookie.
    """
    if result.ok:
        if result.message:
            await flash(request, result.message)
        response = await redirect(request, result.redirect_endpoint or "index.index")
        if result.data is not None:
            await set_auth_cookies(request, response, result.data.id)
        return response
    await flash(request, result.error_message or "")
    return await redirect(request, result.error_endpoint or "auth.login_page")


async def resolve_verify(request: Request, result: AuthResult) -> RedirectResponse:
    """Оформить редирект на страницу подтверждения почты.

    Args:
        request: Текущий HTTP-запрос.
        result: Результат сценария отправки кода.

    Returns:
        RedirectResponse: Редирект с сохранением адреса почты в запросе.
    """
    if result.ok:
        if result.message:
            await flash(request, result.message)
        return await redirect_verify(request, result.redirect_email)
    await flash(request, result.error_message or "")
    return await redirect_verify(request, result.redirect_email)


async def redirect(
    request: Request, endpoint: str, *, query: dict | None = None, **kwargs
) -> RedirectResponse:
    """Собрать редирект 303 на именованный маршрут.

    Args:
        request: Текущий HTTP-запрос.
        endpoint: Имя именованного маршрута.
        query: Параметры строки запроса, если нужны.
        kwargs: Параметры пути именованного маршрута.

    Returns:
        RedirectResponse: Редирект 303.
    """
    url = request.app.url_path_for(endpoint, **kwargs)
    if query:
        query_string = urlencode({key: str(value) for key, value in query.items()})
        url = f"{url}?{query_string}"
    return RedirectResponse(url=url, status_code=SEE_OTHER)


async def redirect_verify(request: Request, email) -> RedirectResponse:
    """Собрать редирект на страницу подтверждения с адресом почты.

    Args:
        request: Текущий HTTP-запрос.
        email: Почта, которую ввёл пользователь.

    Returns:
        RedirectResponse: Редирект 303.
    """
    return RedirectResponse(
        url=(
            f"{request.app.url_path_for('auth.verify_email_page')}"
            f"?email={str(email or '').strip().lower()}"
        ),
        status_code=SEE_OTHER,
    )


async def redirect_confirm(request: Request, token) -> RedirectResponse:
    """Собрать редирект на страницу подтверждения сброса пароля.

    Args:
        request: Текущий HTTP-запрос.
        token: Токен сброса пароля.

    Returns:
        RedirectResponse: Редирект 303.
    """
    return RedirectResponse(
        url=(
            f"{request.app.url_path_for('auth.password_reset_confirm_page')}"
            f"?token={str(token or '').strip()}"
        ),
        status_code=SEE_OTHER,
    )


async def set_auth_cookies(request: Request, response, user_id: int) -> None:
    """Установить access- и refresh-cookie авторизации на ответ.

    Args:
        request: Текущий HTTP-запрос — нужен для сервиса токенов и политики cookie.
        response: Ответ, к которому прикрепляются cookie.
        user_id: Идентификатор аутентифицированного пользователя.
    """
    policy = await resolve_dependency(request, CookiePolicy)
    tokens = await mint_tokens(request, user_id)
    cookie_kwargs = {
        "httponly": True,
        "secure": policy.secure,
        "samesite": policy.samesite,
        "path": "/",
    }
    if policy.domain:
        cookie_kwargs["domain"] = policy.domain
    response.set_cookie(
        ACCESS_TOKEN_COOKIE,
        tokens.access_token,
        max_age=tokens.access_expires_in,
        **cookie_kwargs,
    )
    response.set_cookie(
        REFRESH_TOKEN_COOKIE,
        tokens.refresh_token,
        max_age=tokens.refresh_expires_in,
        **cookie_kwargs,
    )


async def clear_auth_cookies(request: Request, response) -> None:
    """Удалить cookie авторизации с ответом.

    Args:
        request: Текущий HTTP-запрос — нужен для политики cookie.
        response: Ответ, из которого удаляются cookie.
    """
    policy = await resolve_dependency(request, CookiePolicy)
    cookie_kwargs = {
        "httponly": True,
        "secure": policy.secure,
        "samesite": policy.samesite,
        "path": "/",
    }
    if policy.domain:
        cookie_kwargs["domain"] = policy.domain
    response.delete_cookie(ACCESS_TOKEN_COOKIE, **cookie_kwargs)
    response.delete_cookie(REFRESH_TOKEN_COOKIE, **cookie_kwargs)
