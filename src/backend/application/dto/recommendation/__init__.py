"""DTO рекомендаций и запросов к ИИ."""

from backend.application.dto.recommendation.ask_ai_recommendations_command import (
    AskAiRecommendationsCommand,
)
from backend.application.dto.recommendation.recommendations_query import RecommendationsQuery

__all__ = [
    "AskAiRecommendationsCommand",
    "RecommendationsQuery",
]
