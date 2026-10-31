"""Удаление черновика момента просмотра."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeleteViewingMomentCommand:
    """Команда удаления черновика момента.

    Attributes:
        moment_id: Идентификатор черновика.
        user_id: Идентификатор владельца черновика.
    """

    moment_id: int
    user_id: int
