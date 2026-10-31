"""Параметры подбора персонализированных рекомендаций."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecommendationsQuery:
    """Запрос списка рекомендаций для пользователя.

    Attributes:
        user_id: Идентификатор пользователя.
        limit: Максимальное число рекомендаций.
    """

    user_id: int
    limit: int = 5
