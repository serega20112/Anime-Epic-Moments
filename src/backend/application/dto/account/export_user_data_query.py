"""Запрос выгрузки пользовательских данных."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExportUserDataQuery:
    """Намерение получить машиночитаемую копию данных пользователя.

    Attributes:
        user_id: Идентификатор пользователя, чьи данные выгружаются.
    """

    user_id: int
