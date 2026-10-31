"""Преобразователи запросов и ответов для маршрутов реакций."""

from __future__ import annotations

from backend.application.dto import SetEpisodeReactionCommand
from backend.domain import EpisodeReactionSummary
from backend.domain.value_objects.reaction.reaction_type import EpisodeReactionEmoji
from backend.presentation.api.requests.reaction_requests import SetEpisodeReactionRequest
from backend.presentation.api.responses.reaction_responses import (
    EpisodeReactionCountResponse,
    EpisodeReactionsResponse,
)


def map_set_episode_reaction_command(
    body: SetEpisodeReactionRequest, *, user_id: int, anime_id: int
) -> SetEpisodeReactionCommand:
    """Собрать команду изменения реакции из проверенного тела.

    Args:
        body: Проверенное тело реакции.
        user_id: Идентификатор действующего пользователя.
        anime_id: Идентификатор аниме из пути.

    Returns:
        SetEpisodeReactionCommand: Команда с нормализованным типом реакции.
    """
    return SetEpisodeReactionCommand(
        user_id=user_id,
        anime_id=anime_id,
        episode=body.episode,
        reaction_type=str(body.reaction or "").strip(),
        timestamp=float(body.timestamp or 0.0),
        liked=body.liked,
    )


def map_episode_reactions_response(summary: EpisodeReactionSummary) -> EpisodeReactionsResponse:
    """Собрать JSON-сводку реакций на серию.

    Args:
        summary: Доменная сводка реакций со счётчиками и реакцией зрителя.

    Returns:
        EpisodeReactionsResponse: Ответ со счётчиками и реакцией пользователя.
    """
    return EpisodeReactionsResponse(
        counts=[
            EpisodeReactionCountResponse(
                reaction_type=item.reaction_type.value,
                emoji=EpisodeReactionEmoji.for_type(item.reaction_type),
                count=item.count,
            )
            for item in summary.counts
        ],
        user_reaction=summary.user_reaction.value if summary.user_reaction else None,
    )
