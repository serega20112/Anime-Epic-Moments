"""Общий результат сценариев аутентификации.

Сценарии возвращают :class:`AuthResult` вместо исключений домена,
чтобы слой представления только читал итог и выбирал переход.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AuthResult:
    """Итог сценария аутентификации.

    Attributes:
        ok: Признак успешного завершения.
        data: Данные успешного сценария.
        message: Сообщение для пользователя.
        error_message: Текст ошибки.
        error_endpoint: Куда вернуть пользователя при ошибке.
        redirect_endpoint: Куда перейти после успеха.
        redirect_email: Адрес почты, подставляемый в форму.
    """

    ok: bool
    data: Any = None
    message: str | None = None
    error_message: str | None = None
    error_endpoint: str | None = None
    redirect_endpoint: str | None = None
    redirect_email: str | None = None

    @classmethod
    def success(
        cls,
        data: Any = None,
        message: str | None = None,
        redirect_endpoint: str | None = None,
        redirect_email: str | None = None,
    ) -> AuthResult:
        """Собрать успешный результат.

        Args:
            data: Данные успешного сценария.
            message: Сообщение для пользователя.
            redirect_endpoint: Куда перейти после успеха.
            redirect_email: Адрес почты, подставляемый в форму.

        Returns:
            AuthResult: Результат с ``ok=True``.
        """
        return cls(
            ok=True,
            data=data,
            message=message,
            redirect_endpoint=redirect_endpoint,
            redirect_email=redirect_email,
        )

    @classmethod
    def failure(
        cls,
        error_message: str,
        error_endpoint: str,
        redirect_email: str | None = None,
    ) -> AuthResult:
        """Собрать результат с ошибкой.

        Args:
            error_message: Текст ошибки для пользователя.
            error_endpoint: Куда вернуть пользователя при ошибке.
            redirect_email: Адрес почты, подставляемый в форму.

        Returns:
            AuthResult: Результат с ``ok=False``.
        """
        return cls(
            ok=False,
            error_message=error_message,
            error_endpoint=error_endpoint,
            redirect_email=redirect_email,
        )
