"""Изменение профиля пользователя."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UpdateProfileCommand:
    """Команда изменения профиля.

    Attributes:
        user_id: Идентификатор вошедшего пользователя.
        username: Желаемое отображаемое имя.
        avatar_url: Ссылка на аватар.
        status: Текстовый статус профиля.
        show_watch_activity: Показывать ли активность просмотра в профиле.
        show_recent_episodes: Показывать ли недавно просмотренные серии.
    """

    user_id: int
    username: str
    avatar_url: str | None = None
    status: str | None = None
    show_watch_activity: bool = True
    show_recent_episodes: bool = True
