"""Добавление аниме в избранное."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AddFavoriteCommand:
    """Команда добавления аниме в избранное.

    Attributes:
        user_id: Идентификатор пользователя, чьё избранное меняется.
        anime_id: Идентификатор аниме.
        title: Название аниме для снимка карточки.
        description: Описание аниме для снимка карточки.
        cover_url: Ссылка на обложку для снимка карточки.
        genres: Жанры аниме или их JSON-строка из формы.
        original_title: Оригинальное название аниме.
    """

    user_id: int
    anime_id: int
    title: str | None = None
    description: str | None = None
    cover_url: str | None = None
    genres: list[str] | str | None = None
    original_title: str | None = None
