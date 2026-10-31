"""Единый тип результата сценариев прикладного слоя.

Сценарии возвращают :class:`UseCaseResult` вместо исключений домена, чтобы слой
представления только читал итог и строил ответ. Вспомогательные конструкторы —
синхронные ``classmethod``-ы: результат является значением, а не отложенной
асинхронной операцией, поэтому лишнего ``await`` в сценариях быть не должно.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from starlette import status


@dataclass(frozen=True, slots=True)
class UseCaseResult:
    """Итог сценария: успех, HTTP-статус, данные и код ошибки.

    Attributes:
        ok: Признак успешного завершения.
        status_code: HTTP-код, который слой представления положит в ответ.
        data: Данные успешного сценария.
        error: Код ошибки неудачного сценария.
    """

    ok: bool
    status_code: int = status.HTTP_200_OK
    data: Any = None
    error: str | None = None

    @classmethod
    def success(cls, data: Any = None, status_code: int = status.HTTP_200_OK) -> UseCaseResult:
        """Собрать успешный результат.

        Args:
            data: Данные сценария для слоя представления.
            status_code: HTTP-код успешного ответа.

        Returns:
            UseCaseResult: Результат с ``ok=True``.
        """
        return cls(ok=True, status_code=status_code, data=data)

    @classmethod
    def failure(cls, error: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> UseCaseResult:
        """Собрать результат с ошибкой.

        Args:
            error: Код ошибки, различимый слоем представления.
            status_code: HTTP-код ответа с ошибкой.

        Returns:
            UseCaseResult: Результат с ``ok=False`` и без данных.
        """
        return cls(ok=False, status_code=status_code, error=error)
