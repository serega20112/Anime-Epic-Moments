"""Выставление оценки аниме."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SetUserAnimeRatingCommand:
    """Команда выставления оценки аниме.

    Attributes:
        user_id: Идентификатор пользователя.
        anime_id: Идентификатор аниме.
        score: Оценка по десятибалльной шкале.
    """

    user_id: int
    anime_id: int
    score: int
