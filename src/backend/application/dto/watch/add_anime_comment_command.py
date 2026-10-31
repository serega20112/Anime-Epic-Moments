"""Добавление комментария в обсуждение аниме."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AddAnimeCommentCommand:
    """Команда добавления комментария в обсуждение.

    Attributes:
        anime_id: Идентификатор аниме.
        user_id: Идентификатор автора комментария.
        content: Текст комментария.
    """

    anime_id: int
    user_id: int
    content: str
