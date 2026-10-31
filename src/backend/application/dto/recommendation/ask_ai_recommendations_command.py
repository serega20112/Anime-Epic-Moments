"""Запрос рекомендаций у языковой модели."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AskAiRecommendationsCommand:
    """Команда подбора рекомендаций через ИИ.

    Attributes:
        user_id: Идентификатор пользователя.
        query: Свободный текст запроса рекомендаций.
        limit: Максимальное число рекомендаций.
    """

    user_id: int
    query: str
    limit: int = 6
