"""JSON-маршруты входа через Google и привязки/отвязки аккаунта мобильного клиента.

Проверка подлинности ID-токена и решение о создании аккаунта принадлежат
сценарию; маршрут выпускает пару токенов приложения либо сообщает итог
привязки. Вход открыт гостю, привязка и отвязка требуют Bearer-сессии.
"""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.dto.auth import UnlinkGoogleAccountCommand
from backend.application.use_cases import (
    GoogleSignInUseCase,
    LinkGoogleAccountUseCase,
    UnlinkGoogleAccountUseCase,
)
from backend.config import Settings
from backend.presentation.api.auth_responses import mint_tokens
from backend.presentation.api.errors import error_from_result, unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.rate_limit import client_ip, rate_limit
from backend.presentation.api.requests.api_auth_mapper import (
    map_google_sign_in_command,
    map_link_google_command,
    map_token_pair,
)
from backend.presentation.api.requests.api_auth_requests import GoogleTokenRequest
from backend.presentation.api.responses.api_auth_responses import (
    GoogleLinkStatusResponse,
    TokenPairResponse,
)
from backend.presentation.api.v1.auth.api_common import ERROR_RESPONSES, client_ip_key
from backend.utils import log_security_event

google_router = APIRouter(route_class=DishkaRoute)


@google_router.post(
    "/google",
    name="api_auth.google_sign_in",
    response_model=TokenPairResponse,
    responses=ERROR_RESPONSES,
)
@rate_limit(
    scope="auth_login",
    limit=Settings.auth_login_attempts_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=client_ip_key,
)
async def google_sign_in(
    request: Request,
    body: GoogleTokenRequest,
    use_case: FromDishka[GoogleSignInUseCase],
):
    """Войти через Google и выдать пару токенов приложения.

    Пользователь ищется по стабильному идентификатору Google либо по почте; при
    отсутствии аккаунта он создаётся с служебным паролем. Проверка подлинности
    ID-токена и решение о создании аккаунта принадлежат сценарию.

    Args:
        request: Текущий HTTP-запрос.
        body: Тело с ID-токеном Google.
        use_case: Сценарий входа через Google.

    Returns:
        TokenPairResponse | Response: Пара токенов либо единое тело отказа.
    """
    result = await use_case.execute(map_google_sign_in_command(body))
    if not result.ok:
        return error_from_result(result)
    user = result.data
    log_security_event(
        event="login_success",
        user_id=str(user.id),
        email=user.email,
        ip_address=await client_ip(request),
        details={"channel": "google"},
    )
    return map_token_pair(await mint_tokens(request, int(user.id)), user)


@google_router.post(
    "/google/link",
    name="api_auth.google_link",
    response_model=GoogleLinkStatusResponse,
    responses=ERROR_RESPONSES,
)
async def link_google(
    request: Request,
    body: GoogleTokenRequest,
    use_case: FromDishka[LinkGoogleAccountUseCase],
):
    """Привязать подтверждённый аккаунт Google к пользователю сессии.

    Args:
        request: Текущий HTTP-запрос с заголовком Authorization.
        body: Тело с ID-токеном Google.
        use_case: Сценарий привязки Google.

    Returns:
        GoogleLinkStatusResponse | Response: Признак привязки либо тело отказа.
    """
    user = await get_current_user(request)
    if user is None:
        return unauthorized_error()
    result = await use_case.execute(map_link_google_command(body, user_id=user.id))
    if not result.ok:
        return error_from_result(result)
    return GoogleLinkStatusResponse(google_linked=True)


@google_router.post(
    "/google/unlink",
    name="api_auth.google_unlink",
    response_model=GoogleLinkStatusResponse,
    responses=ERROR_RESPONSES,
)
async def unlink_google(
    request: Request,
    use_case: FromDishka[UnlinkGoogleAccountUseCase],
):
    """Отвязать аккаунт Google от пользователя сессии.

    Args:
        request: Текущий HTTP-запрос с заголовком Authorization.
        use_case: Сценарий отвязки Google.

    Returns:
        GoogleLinkStatusResponse | Response: Признак привязки либо тело отказа.
    """
    user = await get_current_user(request)
    if user is None:
        return unauthorized_error()
    result = await use_case.execute(UnlinkGoogleAccountCommand(user_id=user.id))
    if not result.ok:
        return error_from_result(result)
    return GoogleLinkStatusResponse(google_linked=False)
