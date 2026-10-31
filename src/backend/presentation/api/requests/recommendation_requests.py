"""Схемы тел запросов маршрутов рекомендаций."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

QUERY_MAX_LENGTH = 400
LIMIT_MAX = 10


class AskAiRecommendationsRequest(BaseModel):
    """Тело запроса рекомендаций у ИИ.

    Attributes:
        query: Свободный текстовый запрос зрителя.
        limit: Запрошенное число рекомендаций.
    """

    model_config = ConfigDict(extra="ignore")

    query: str = Field(default="", max_length=QUERY_MAX_LENGTH)
    limit: int | None = Field(default=None, ge=1, le=LIMIT_MAX)
