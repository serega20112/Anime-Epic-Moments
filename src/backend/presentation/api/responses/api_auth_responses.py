"""Модели ответов JSON-аутентификации для мобильного клиента."""

from __future__ import annotations

from pydantic import BaseModel

TOKEN_TYPE_BEARER = "bearer"


class TokenPairResponse(BaseModel):
    """Пара токенов с данными владельца сессии.

    Attributes:
        access_token: Коротко живущий токен доступа для заголовка Authorization.
        refresh_token: Длительно живущий токен для продления пары.
        token_type: Схема авторизации, всегда ``bearer``.
        access_expires_in: Время жизни access-токена в секундах.
        refresh_expires_in: Время жизни refresh-токена в секундах.
        user_id: Идентификатор аутентифицированного пользователя.
        username: Отображаемое имя пользователя.
        email: Адрес почты пользователя.
    """

    access_token: str
    refresh_token: str
    token_type: str = TOKEN_TYPE_BEARER
    access_expires_in: int
    refresh_expires_in: int
    user_id: int
    username: str
    email: str


class TokenRevokedResponse(BaseModel):
    """Признак отзыва токенов сессии.

    Attributes:
        revoked: True, если токены добавлены в список отозванных.
    """

    revoked: bool


class GoogleLinkStatusResponse(BaseModel):
    """Итог привязки или отвязки аккаунта Google.

    Attributes:
        google_linked: Привязан ли аккаунт к Google после операции.
    """

    google_linked: bool
