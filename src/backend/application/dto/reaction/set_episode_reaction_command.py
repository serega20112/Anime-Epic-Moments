"""Постановка и снятие реакции на моменте серии."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SetEpisodeReactionCommand:
    """Команда изменения реакции на серии.

    Attributes:
        user_id: Идентификатор действующего пользователя.
        anime_id: Идентификатор аниме.
        episode: Номер серии.
        reaction_type: Тип реакции.
        timestamp: Отметка момента в секундах.
        liked: True — поставить реакцию, False — снять.
    """

    user_id: int
    anime_id: int
    episode: int
    reaction_type: str
    timestamp: float = 0.0
    liked: bool = True
