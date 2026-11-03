"""Запрос библиотеки просмотра пользователя."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetUserLibraryQuery:
    """Запрос записей дневника пользователя по статусу просмотра.

    Attributes:
        user_id: Идентификатор пользователя сессии.
        status: Требуемый статус дневника; пустая строка означает весь дневник.
    """

    user_id: int
    status: str = ""
