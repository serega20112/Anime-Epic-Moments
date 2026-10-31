"""Преобразователи запросов для команд рекомендаций."""

from __future__ import annotations

from backend.application.dto import AskAiRecommendationsCommand
from backend.presentation.api.requests.recommendation_requests import (
    AskAiRecommendationsRequest,
)

ASK_LIMIT_DEFAULT = 6
ASK_LIMIT_MIN = 1
ASK_LIMIT_MAX = 10


def map_ask_ai_command(
    body: AskAiRecommendationsRequest, *, user_id: int
) -> AskAiRecommendationsCommand:
    """Собрать команду запроса к ИИ из проверенного тела.

    Args:
        body: Проверенное тело запроса рекомендаций.
        user_id: Идентификатор пользователя сессии.

    Returns:
        AskAiRecommendationsCommand: Команда с нормализованным запросом и лимитом.
    """
    return AskAiRecommendationsCommand(
        user_id=user_id,
        query=str(body.query or "").strip(),
        limit=_clamp_limit(body.limit),
    )


def _clamp_limit(value: int | None) -> int:
    """Ограничить размер выдачи допустимым диапазоном.

    Args:
        value: Запрошенное число рекомендаций либо None.

    Returns:
        int: Число рекомендаций внутри диапазона.
    """
    if value is None:
        return ASK_LIMIT_DEFAULT
    return max(ASK_LIMIT_MIN, min(value, ASK_LIMIT_MAX))
