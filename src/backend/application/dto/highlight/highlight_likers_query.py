"""Параметры выборки пользователей, поставивших лайк хайлайту."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HighlightLikersQuery:
    """Запрос пользователей, лайкнувших хайлайт.

    Attributes:
        highlight_id: Идентификатор хайлайта.
        limit: Максимальное число пользователей.
    """

    highlight_id: int
    limit: int = 20
