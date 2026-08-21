"""Thin HTTP routes for episode reactions on the anime watch page."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.application.dto import (
    GetEpisodeReactionsQuery,
    SetEpisodeReactionCommand,
)
from backend.application.use_cases import (
    GetEpisodeReactionsUseCase,
    SetEpisodeReactionUseCase,
)
from backend.domain.value_objects.reaction.reaction_type import EpisodeReactionEmoji
from backend.presentation.api.helpers import get_current_user, read_payload

reaction_router = APIRouter(prefix="/watch", route_class=DishkaRoute)
reaction_bp = reaction_router


async def _reaction_payload(summary) -> dict:
    """Build the JSON payload for an episode reaction summary.

    Args:
        summary: Episode reaction summary.

    Returns:
        dict: Serialized reaction state.
    """
    counts = [
        {
            "reaction_type": item.reaction_type.value,
            "emoji": EpisodeReactionEmoji.for_type(item.reaction_type),
            "count": item.count,
        }
        for item in summary.counts
    ]
    return {
        "counts": counts,
        "user_reaction": summary.user_reaction.value if summary.user_reaction else None,
    }


@reaction_router.get("/{anime_id}/reactions", name="watch.get_episode_reactions")
async def get_episode_reactions(
    request: Request,
    anime_id: int,
    use_case: FromDishka[GetEpisodeReactionsUseCase],
):
    """Return reaction counts for an episode and the viewer's own reaction.

    Args:
        request: Incoming HTTP request with the episode query param.
        anime_id: Anime ID from path.
        use_case: Get episode reactions use case.

    Returns:
        JSONResponse: Reaction state or an error.
    """
    user = await get_current_user(request)
    try:
        episode = int(request.query_params.get("episode") or 1)
    except (TypeError, ValueError):
        episode = 0
    result = await use_case.execute(
        GetEpisodeReactionsQuery(
            anime_id=anime_id,
            episode=episode,
            user_id=user.id if user else None,
        )
    )
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return await _reaction_payload(result.data)


@reaction_router.post("/{anime_id}/reactions", name="watch.set_episode_reaction")
async def set_episode_reaction(
    request: Request,
    anime_id: int,
    use_case: FromDishka[SetEpisodeReactionUseCase],
):
    """Set or remove a reaction on an episode.

    Args:
        request: Incoming HTTP request with JSON payload.
        anime_id: Anime ID from path.
        use_case: Set episode reaction use case.

    Returns:
        JSONResponse: Updated reaction state or an error.
    """
    user = await get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    payload = await read_payload(request)
    try:
        episode = int(payload.get("episode") or 1)
    except (TypeError, ValueError):
        episode = 0
    try:
        timestamp = float(payload.get("timestamp") or 0.0)
    except (TypeError, ValueError):
        timestamp = 0.0
    command = SetEpisodeReactionCommand(
        user_id=user.id,
        anime_id=anime_id,
        episode=episode,
        reaction_type=str(payload.get("reaction") or "").strip(),
        timestamp=timestamp,
        liked=request.method == "POST",
    )
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return await _reaction_payload(result.data)
