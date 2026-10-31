"""Схемы тел запросов JSON-аутентификации для мобильного клиента."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

EMAIL_MAX_LENGTH = 254
PASSWORD_MAX_LENGTH = 128
TOKEN_MAX_LENGTH = 4096


class CredentialsRequest(BaseModel):
    """Тело входа по почте и паролю.

    Attributes:
        email: Адрес почты пользователя.
        password: Пароль в открытом виде.
    """

    model_config = ConfigDict(extra="ignore")

    email: str = Field(min_length=3, max_length=EMAIL_MAX_LENGTH)
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)


class RefreshTokenRequest(BaseModel):
    """Тело продления пары токенов.

    Attributes:
        refresh_token: Ранее выданный refresh-токен.
    """

    model_config = ConfigDict(extra="ignore")

    refresh_token: str = Field(min_length=10, max_length=TOKEN_MAX_LENGTH)


class RevokeTokensRequest(BaseModel):
    """Тело отзыва токенов при выходе.

    Attributes:
        refresh_token: Refresh-токен, который нужно отозвать вместе с access-токеном.
    """

    model_config = ConfigDict(extra="ignore")

    refresh_token: str = Field(min_length=10, max_length=TOKEN_MAX_LENGTH)
