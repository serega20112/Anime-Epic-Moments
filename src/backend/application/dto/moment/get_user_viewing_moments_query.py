"""Запрос черновиков моментов пользователя."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetUserViewingMomentsQuery:
    """Запрос списка черновиков моментов.

    Attributes:
        user_id: Идентификатор владельца черновиков.
    """

    user_id: int
