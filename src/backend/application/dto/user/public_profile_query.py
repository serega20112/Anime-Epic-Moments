"""Параметры запроса публичного профиля."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PublicProfileQuery:
    """Запрос публичного обзора профиля с отметкой подписки.

    Attributes:
        profile_user_id: Идентификатор пользователя, чей профиль открывается.
        viewer_user_id: Идентификатор зрителя либо None для гостя.
    """

    profile_user_id: int
    viewer_user_id: int | None = None
