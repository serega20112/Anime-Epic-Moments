"""Результат сценария обращения в поддержку.

Сценарий возвращает :class:`CreateSupportTicketResult` вместо исключений
домена, чтобы слой представления только читал итог, показывал сообщение
и выбирал HTTP-переход.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from starlette import status


@dataclass(frozen=True, slots=True)
class CreateSupportTicketResult:
    """Итог сценария: обращение в поддержку."""

    ok: bool
    status_code: int = status.HTTP_200_OK
    data: Any = None
    error_message: str | None = None
    message: str | None = None
    service_unavailable: bool = False

    @classmethod
    def success(
        cls,
        data: Any,
        message: str | None = None,
        service_unavailable: bool = False,
    ) -> CreateSupportTicketResult:
        """Собрать успешный результат.

        Args:
            data: Данные сценария для слоя представления.
            message: Сообщение для пользователя.
            service_unavailable: Признак того, что письмо доставлено не было.

        Returns:
            CreateSupportTicketResult: Результат с ``ok=True``.
        """
        return cls(
            ok=True,
            status_code=status.HTTP_200_OK,
            data=data,
            message=message,
            service_unavailable=service_unavailable,
        )

    @classmethod
    def failure(
        cls, error_message: str, status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> CreateSupportTicketResult:
        """Собрать результат с ошибкой.

        Args:
            error_message: Текст ошибки для пользователя.
            status_code: HTTP-код ответа с ошибкой.

        Returns:
            CreateSupportTicketResult: Результат с ``ok=False``.
        """
        return cls(ok=False, status_code=status_code, error_message=error_message)
