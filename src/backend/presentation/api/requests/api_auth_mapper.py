"""Преобразователи тел и ответов JSON-аутентификации."""

from __future__ import annotations

from backend.application.dto import LoginCommand, LogoutCommand, RefreshSessionCommand
from backend.domain import User
from backend.domain.policies.user_credentials_policy import normalize_email
from backend.presentation.api.auth_responses import IssuedTokens
from backend.presentation.api.requests.api_auth_requests import (
    CredentialsRequest,
    RefreshTokenRequest,
    RevokeTokensRequest,
)
from backend.presentation.api.responses.api_auth_responses import TokenPairResponse


def map_credentials_command(body: CredentialsRequest) -> LoginCommand:
    """Собрать команду входа из проверенного тела.

    Args:
        body: Тело с почтой и паролем.

    Returns:
        LoginCommand: Команда с нормализованным адресом почты.
    """
    return LoginCommand(email=normalize_email(body.email), password=str(body.password or ""))


def map_refresh_command(body: RefreshTokenRequest) -> RefreshSessionCommand:
    """Собрать команду продления из проверенного тела.

    Args:
        body: Тело с ранее выданным refresh-токеном.

    Returns:
        RefreshSessionCommand: Команда с обрезанным значением токена.
    """
    return RefreshSessionCommand(refresh_token=str(body.refresh_token or "").strip())


def map_revoke_command(body: RevokeTokensRequest, *, access_token: str) -> LogoutCommand:
    """Собрать команду выхода из тела и разобранного заголовка.

    Args:
        body: Тело с отзываемым refresh-токеном.
        access_token: Значение access-токена из заголовка Authorization.

    Returns:
        LogoutCommand: Команда отзыва обеих токенов.
    """
    return LogoutCommand(
        access_token=str(access_token or "").strip(),
        refresh_token=str(body.refresh_token or "").strip(),
    )


def map_token_pair(tokens: IssuedTokens, user: User) -> TokenPairResponse:
    """Собрать ответ с парой токенов и данными владельца сессии.

    Args:
        tokens: Выпущенная пара токенов и времена их жизни.
        user: Аутентифицированный пользователь.

    Returns:
        TokenPairResponse: Ответ для мобильного клиента.
    """
    return TokenPairResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        access_expires_in=tokens.access_expires_in,
        refresh_expires_in=tokens.refresh_expires_in,
        user_id=int(user.id or 0),
        username=user.username,
        email=user.email,
    )
