"""Запрос коллекций пользователя."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetUserCollectionsQuery:
    """Запрос коллекций конкретного пользователя.

    Attributes:
        user_id: Идентификатор пользователя.
    """

    user_id: int
