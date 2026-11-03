"""JSON-маршруты выдачи, продления и отзыва токенов мобильного клиента.

Поверхность отвечает только JSON и работает через заголовок
``Authorization: Bearer``: куки не ставятся, CSRF-проверка к таким запросам не
применяется. Сценарии те же, что и у браузерных форм, поэтому правила
блокировки перебора и отзыв токенов не дублируются.
"""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.use_cases import (
    LoginUserUseCase,
    LogoutUserUseCase,
    RefreshSessionUseCase,
)
from backend.config import Settings
from backend.presentation.api.auth_responses import mint_tokens
from backend.presentation.api.errors import (
    ERROR_UNAUTHORIZED,
    error_response,
    unauthorized_error,
)
from backend.presentation.api.rate_limit import client_ip, rate_limit
from backend.presentation.api.requests.api_auth_mapper import (
    map_credentials_command,
    map_refresh_command,
    map_revoke_command,
    map_token_pair,
)
from backend.presentation.api.requests.api_auth_requests import (
    CredentialsRequest,
    RefreshTokenRequest,
    RevokeTokensRequest,
)
from backend.presentation.api.responses.api_auth_responses import (
    TokenPairResponse,
    TokenRevokedResponse,
)
from backend.presentation.api.v1.auth.api_common import ERROR_RESPONSES, client_ip_key
from backend.presentation.security_helpers import extract_bearer_token
from backend.utils import log_security_event

token_router = APIRouter(route_class=DishkaRoute)

LOGIN_DENIED_MESSAGE = "Неверная почта или пароль"
SESSION_EXPIRED_MESSAGE = "Сессия истекла"
API_TOKEN_REQUIRED_MESSAGE = "Требуется Bearer-токен"


@token_router.post(
    "/token",
    name="api_auth.issue_token",
    response_model=TokenPairResponse,
    responses=ERROR_RESPONSES,
)
@rate_limit(
    scope="auth_login",
    limit=Settings.auth_login_attempts_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=client_ip_key,
)
async def issue_token(
    request: Request,
    body: CredentialsRequest,
    use_case: FromDishka[LoginUserUseCase],
):
    """Выдать пару токенов по почте и паролю.

    Args:
        request: Текущий HTTP-запрос.
        body: Проверенное тело учётных данных.
        use_case: Сценарий входа, общий с браузерной формой.

    Returns:
        TokenPairResponse | Response: Пара токенов либо единое тело отказа.
    """
    command = map_credentials_command(body)
    result = await use_case.execute(command)
    ip_address = await client_ip(request)
    if not result.ok:
        log_security_event(event="login_failed", email=command.email, ip_address=ip_address)
        return unauthorized_error(result.error_message or LOGIN_DENIED_MESSAGE)
    log_security_event(
        event="login_success",
        user_id=str(result.data.id),
        email=command.email,
        ip_address=ip_address,
        details={"channel": "api"},
    )
    return map_token_pair(await mint_tokens(request, int(result.data.id)), result.data)


@token_router.post(
    "/token/refresh",
    name="api_auth.refresh_token",
    response_model=TokenPairResponse,
    responses=ERROR_RESPONSES,
)
@rate_limit(
    scope="api_auth_refresh",
    limit=Settings.auth_api_refresh_attempts_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=client_ip_key,
)
async def refresh_token(
    request: Request,
    body: RefreshTokenRequest,
    use_case: FromDishka[RefreshSessionUseCase],
):
    """Продлить сессию мобильному клиенту с ротацией refresh-токена.

    Args:
        request: Текущий HTTP-запрос.
        body: Тело с ранее выданным refresh-токеном.
        use_case: Сценарий продления, общий с браузерной cookie-схемой.

    Returns:
        TokenPairResponse | Response: Новая пара токенов либо единое тело отказа.
    """
    result = await use_case.execute(map_refresh_command(body))
    if not result.ok:
        return error_response(
            ERROR_UNAUTHORIZED,
            result.error_message or SESSION_EXPIRED_MESSAGE,
            HTTPStatus.UNAUTHORIZED,
        )
    return map_token_pair(await mint_tokens(request, int(result.data.id)), result.data)


@token_router.post(
    "/token/revoke",
    name="api_auth.revoke_token",
    response_model=TokenRevokedResponse,
    responses=ERROR_RESPONSES,
)
async def revoke_token(
    request: Request,
    body: RevokeTokensRequest,
    use_case: FromDishka[LogoutUserUseCase],
):
    """Отозвать access- и refresh-токены мобильного клиента.

    Метод POST, а не DELETE: отзыв требует тела с refresh-токеном, а ответ 204
    тело запроса не допускает.

    Args:
        request: Текущий HTTP-запрос с заголовком Authorization.
        body: Тело с отзываемым refresh-токеном.
        use_case: Сценарий выхода с записью в список отозванных.

    Returns:
        TokenRevokedResponse | Response: Признак отзыва либо единое тело отказа 401.
    """
    access_token = extract_bearer_token(request)
    if access_token is None:
        return unauthorized_error(API_TOKEN_REQUIRED_MESSAGE)
    await use_case.execute(map_revoke_command(body, access_token=access_token))
    return TokenRevokedResponse(revoked=True)
