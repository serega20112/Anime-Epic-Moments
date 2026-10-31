"""Маршруты сессии: вход, регистрация, выход, обновление токенов."""

from __future__ import annotations

import logging
from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.application.dto import LogoutCommand, RefreshSessionCommand
from backend.application.use_cases import LogoutUserUseCase, RefreshSessionUseCase
from backend.application.use_cases.auth.login_register.login_user import LoginUserUseCase
from backend.application.use_cases.auth.verification.request_email_verification import (
    RequestEmailVerificationUseCase,
)
from backend.config import Settings
from backend.presentation.api.auth_responses import (
    clear_auth_cookies,
    redirect,
    redirect_verify,
    resolve_auth,
    resolve_verify,
    set_auth_cookies,
)
from backend.presentation.api.errors import ERROR_UNAUTHORIZED, error_response
from backend.presentation.api.rate_limit import client_ip, rate_limit
from backend.presentation.api.requests.auth_mapper import (
    FormValidationError,
    map_login_command,
    map_register_command,
)
from backend.presentation.api.responses.auth_responses import SessionRefreshResponse
from backend.presentation.web import flash, render_template
from backend.utils import log_security_event

session_router = APIRouter(route_class=DishkaRoute)

logger = logging.getLogger("anime_epic_moments")

UNAUTHORIZED = HTTPStatus.UNAUTHORIZED
REFRESH_RESPONSES = {
    "200": {"content": {"application/json": {"schema": SessionRefreshResponse.model_json_schema()}}}
}


async def _client_ip_key(request: Request) -> str:
    """Собрать субъект ограничения частоты по IP клиента.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        str: IP-адрес клиента.
    """
    return await client_ip(request)


@session_router.get("/login", name="auth.login_page")
async def login_page(request: Request):
    """Отрисовать страницу входа.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        HTMLResponse: Страница входа.
    """
    return await render_template(request, "auth/login.html")


@session_router.get("/register", name="auth.register_page")
async def register_page(request: Request):
    """Отрисовать страницу регистрации.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        HTMLResponse: Страница регистрации.
    """
    return await render_template(request, "auth/register.html")


@session_router.post("/login", name="auth.login_user")
@rate_limit(
    scope="auth_login",
    limit=Settings.auth_login_attempts_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=_client_ip_key,
    response_mode="redirect",
    redirect_endpoint="auth.login_page",
)
async def login_user(request: Request, use_case: FromDishka[LoginUserUseCase]):
    """Проверить учётные данные и установить куки сессии.

    Args:
        request: Текущий HTTP-запрос.
        use_case: Сценарий входа.

    Returns:
        RedirectResponse: Переход на главную либо обратно на форму входа.
    """
    form = await request.form()
    try:
        command = map_login_command(form)
    except FormValidationError as error:
        await flash(request, str(error))
        return await redirect(request, "auth.login_page")
    result = await use_case.execute(command)
    if result.ok:
        log_security_event(
            event="login_success",
            user_id=str(result.data.id),
            email=command.email,
            ip_address=await client_ip(request),
        )
    else:
        log_security_event(
            event="login_failed",
            email=command.email,
            ip_address=await client_ip(request),
        )
    return await resolve_auth(request, result)


@session_router.post("/register", name="auth.register_user")
@rate_limit(
    scope="auth_register",
    limit=Settings.auth_register_attempts_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=_client_ip_key,
    response_mode="redirect",
    redirect_endpoint="auth.register_page",
)
async def register_user(request: Request, use_case: FromDishka[RequestEmailVerificationUseCase]):
    """Начать регистрацию запросом кода подтверждения email.

    Args:
        request: Текущий HTTP-запрос.
        use_case: Сценарий запроса подтверждения email.

    Returns:
        RedirectResponse: Переход на страницу подтверждения либо обратно.
    """
    form = await request.form()
    try:
        command = map_register_command(form)
    except FormValidationError as error:
        return await redirect_verify(request, str(error))
    logger.info(
        "register_verification_requested email=%s ip=%s",
        command.email,
        await client_ip(request),
    )
    result = await use_case.execute(command)
    return await resolve_verify(request, result)


@session_router.post("/logout", name="auth.logout_user")
async def logout_user(request: Request, use_case: FromDishka[LogoutUserUseCase]):
    """Завершить сессию и отозвать токены.

    Args:
        request: Текущий HTTP-запрос.
        use_case: Сценарий выхода.

    Returns:
        RedirectResponse: Переход на главную страницу.
    """
    await use_case.execute(
        LogoutCommand(
            access_token=str(request.cookies.get("access_token") or "").strip(),
            refresh_token=str(request.cookies.get("refresh_token") or "").strip(),
        )
    )
    response = await redirect(request, "index.index")
    await clear_auth_cookies(request, response)
    return response


@session_router.post("/refresh", name="auth.refresh_session", responses=REFRESH_RESPONSES)
async def refresh_session(request: Request, use_case: FromDishka[RefreshSessionUseCase]):
    """Обновить пару токенов по действующей refresh-cookie.

    Args:
        request: Текущий HTTP-запрос.
        use_case: Сценарий обновления сессии.

    Returns:
        JSONResponse: Ответ со статусом и новыми куками.
    """
    result = await use_case.execute(
        RefreshSessionCommand(refresh_token=str(request.cookies.get("refresh_token") or "").strip())
    )
    if not result.ok:
        return error_response(
            ERROR_UNAUTHORIZED,
            result.error_message or "Сессия истекла",
            HTTPStatus.UNAUTHORIZED,
        )
    response = JSONResponse({"status": "ok"})
    await set_auth_cookies(request, response, int(result.data.id))
    return response
