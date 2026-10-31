"""Запрос обзора профиля пользователя."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProfileOverviewQuery:
    """Параметры сборки обзора профиля.

    Attributes:
        user_id: Идентификатор пользователя, чей профиль собирается.
    """

    user_id: int
