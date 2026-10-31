"""Зависимости аутентификации HTTP-роутов.

Идентификатор пользователя берётся только из аутентифицированной сессии,
которую наполняет мидлварь :func:`backend.presentation.security_helpers.load_user`.
Значения ``user_id`` из пути или тела запроса клиенту не доверяются: они
сравниваются с сессией, а не подставляются в сценарий (задача S1).

Отказы оформляются доменными исключениями :class:`AuthenticationError` и
:class:`AuthorizationError`, поэтому статус и тело ``{code, message, details}``
считываются единым словарём :data:`backend.presentation.api.errors.ERROR_STATUS`.
"""

from __future__ import annotations

from fastapi import Request

from backend.domain.exceptions import AuthenticationError, AuthorizationError

LOGIN_REQUIRED_MESSAGE = "Требуется вход в аккаунт"
FORBIDDEN_MESSAGE = "Нет прав на этот ресурс"


async def get_optional_user_id(request: Request) -> int | None:
    """Вернуть идентификатор пользователя сессии, гость — ``None``.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        int | None: Идентификатор авторизованного пользователя либо None.
    """
    user_id = getattr(getattr(request.state, "user", None), "id", None)
    return int(user_id) if isinstance(user_id, int) else None


async def get_current_user_id(request: Request) -> int:
    """Вернуть идентификатор аутентифицированного пользователя.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        int: Идентификатор пользователя сессии.

    Raises:
        AuthenticationError: 401, когда запрос анонимный.
    """
    user_id = await get_optional_user_id(request)
    if user_id is None:
        raise AuthenticationError(LOGIN_REQUIRED_MESSAGE)
    return user_id


async def require_self(request: Request, user_id: int) -> int:
    """Проверить, что идентификатор из пути принадлежит пользователю сессии.

    Используется на приватных роутах, где путь исторически содержит
    ``{user_id}``: значение из пути не подставляется в сценарий, а служит
    заявкой, которую сверяют с сессией.

    Args:
        request: Текущий HTTP-запрос.
        user_id: Идентификатор пользователя из пути запроса.

    Returns:
        int: Идентификатор пользователя сессии.

    Raises:
        AuthenticationError: 401 для анонимного запроса.
        AuthorizationError: 403 при несовпадении с пользователем сессии.
    """
    current_user_id = await get_current_user_id(request)
    if user_id != current_user_id:
        raise AuthorizationError(FORBIDDEN_MESSAGE)
    return current_user_id
