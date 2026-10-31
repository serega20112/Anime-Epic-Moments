"""Схемы тел запросов маршрутов реакций на серии."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

REACTION_MAX_LENGTH = 40


class SetEpisodeReactionRequest(BaseModel):
    """Тело постановки или снятия реакции на моменте серии.

    Attributes:
        episode: Номер серии.
        reaction: Тип реакции.
        timestamp: Отметка момента в секундах.
        liked: True — поставить реакцию, False — снять.
    """

    model_config = ConfigDict(extra="ignore")

    episode: int = Field(default=1, ge=1)
    reaction: str = Field(default="", max_length=REACTION_MAX_LENGTH)
    timestamp: float = Field(default=0.0, ge=0)
    liked: bool = True
