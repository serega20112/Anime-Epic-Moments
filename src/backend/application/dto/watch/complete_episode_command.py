"""Продвижение прогресса после просмотра серии."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CompleteEpisodeCommand:
    """Команда отметки просмотренной серии.

    Attributes:
        user_id: Идентификатор действующего пользователя.
        anime_id: Идентификатор аниме.
        episode: Номер просмотренной серии.
    """

    user_id: int
    anime_id: int
    episode: int | None
