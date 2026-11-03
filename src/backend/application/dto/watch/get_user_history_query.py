"""Запрос истории просмотров пользователя."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetUserHistoryQuery:
    """Запрос последних сессий просмотра пользователя.

    Attributes:
        user_id: Идентификатор пользователя сессии.
        limit: Максимальное число записей истории.
    """

    user_id: int
    limit: int = 50
