"""Параметры запроса состояния реакций на серию."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetEpisodeReactionsQuery:
    """Параметры чтения реакций на серии.

    Attributes:
        anime_id: Идентификатор аниме.
        episode: Номер серии.
        user_id: Идентификатор зрителя для отметки его реакции.
    """

    anime_id: int
    episode: int
    user_id: int | None = None
