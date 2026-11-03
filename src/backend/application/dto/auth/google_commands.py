"""Команды входа и привязки аккаунта Google."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GoogleSignInCommand:
    """Команда входа через Google по ID-токену.

    Attributes:
        id_token: JWT-токен аккаунта Google, полученный мобильным клиентом.
    """

    id_token: str


@dataclass(frozen=True, slots=True)
class LinkGoogleAccountCommand:
    """Команда привязать Google-аккаунт к существующему пользователю.

    Attributes:
        user_id: Идентификатор пользователя сессии.
        id_token: ID-токен аккаунта Google для привязки.
    """

    user_id: int
    id_token: str


@dataclass(frozen=True, slots=True)
class UnlinkGoogleAccountCommand:
    """Команда отвязать Google-аккаунт от пользователя.

    Attributes:
        user_id: Идентификатор пользователя сессии.
    """

    user_id: int
