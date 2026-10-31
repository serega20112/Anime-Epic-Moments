"""Параметры выборки комментариев хайлайта."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HighlightCommentsQuery:
    """Запрос комментариев к хайлайту.

    Attributes:
        highlight_id: Идентификатор хайлайта.
        limit: Максимальное число комментариев.
    """

    highlight_id: int
    limit: int = 20
