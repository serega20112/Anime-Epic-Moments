"""Параметры выборки уведомлений по хайлайтам пользователя."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HighlightNotificationsQuery:
    """Запрос недавней активности по хайлайтам пользователя.

    Attributes:
        user_id: Идентификатор владельца хайлайтов.
        limit: Максимальное число уведомлений.
    """

    user_id: int
    limit: int = 20
