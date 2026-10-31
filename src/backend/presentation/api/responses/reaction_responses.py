"""Модели ответов JSON-маршрутов реакций на серии."""

from __future__ import annotations

from pydantic import BaseModel


class EpisodeReactionCountResponse(BaseModel):
    """Счётчик одной реакции на моменте серии.

    Attributes:
        reaction_type: Тип реакции.
        emoji: Эмодзи-представление реакции.
        count: Число пользователей с такой реакцией.
    """

    reaction_type: str
    emoji: str
    count: int


class EpisodeReactionsResponse(BaseModel):
    """Сводка реакций серии с реакцией текущего зрителя.

    Attributes:
        counts: Счётчики реакций по типам.
        user_reaction: Тип реакции зрителя либо None, если её нет.
    """

    counts: list[EpisodeReactionCountResponse]
    user_reaction: str | None = None
