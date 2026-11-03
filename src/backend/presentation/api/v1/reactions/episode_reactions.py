"""Тонкие HTTP-маршруты реакций на серии страницы просмотра."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Query, Request

from backend.application.dto import GetEpisodeReactionsQuery
from backend.application.use_cases import (
    GetEpisodeReactionsUseCase,
    SetEpisodeReactionUseCase,
)
from backend.presentation.api.errors import (
    ErrorResponse,
    error_from_result,
    unauthorized_error,
)
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.reaction_mapper import (
    map_episode_reactions_response,
    map_set_episode_reaction_command,
)
from backend.presentation.api.requests.reaction_requests import SetEpisodeReactionRequest
from backend.presentation.api.responses.reaction_responses import EpisodeReactionsResponse

episode_reactions_router = APIRouter(route_class=DishkaRoute)

DEFAULT_EPISODE = 1

_ERROR_RESPONSES = {
    "400": {"model": ErrorResponse},
    "401": {"model": ErrorResponse},
    "404": {"model": ErrorResponse},
}


@episode_reactions_router.get(
    "/{anime_id}/reactions",
    name="watch.get_episode_reactions",
    response_model=EpisodeReactionsResponse,
    responses=_ERROR_RESPONSES,
)
async def get_episode_reactions(
    request: Request,
    anime_id: int,
    use_case: FromDishka[GetEpisodeReactionsUseCase],
    episode: int = Query(default=DEFAULT_EPISODE, ge=1),
):
    """Вернуть счётчики реакций серии и реакцию зрителя.

    Args:
        request: Текущий HTTP-запрос.
        anime_id: Идентификатор аниме из пути.
        use_case: Сценарий чтения реакций серии.
        episode: Номер серии из параметра запроса.

    Returns:
        EpisodeReactionsResponse | Response: Сводка реакций либо тело ошибки.
    """
    user = await get_current_user(request)
    result = await use_case.execute(
        GetEpisodeReactionsQuery(
            anime_id=anime_id,
            episode=episode,
            user_id=user.id if user else None,
        )
    )
    if not result.ok:
        return error_from_result(result)
    return map_episode_reactions_response(result.data)


@episode_reactions_router.post(
    "/{anime_id}/reactions",
    name="watch.set_episode_reaction",
    response_model=EpisodeReactionsResponse,
    responses=_ERROR_RESPONSES,
)
async def set_episode_reaction(
    request: Request,
    anime_id: int,
    body: SetEpisodeReactionRequest,
    use_case: FromDishka[SetEpisodeReactionUseCase],
):
    """Поставить или снять реакцию на серию.

    Args:
        request: Текущий HTTP-запрос.
        anime_id: Идентификатор аниме из пути.
        body: Проверенное тело реакции.
        use_case: Сценарий изменения реакции на серии.

    Returns:
        EpisodeReactionsResponse | Response: Обновлённая сводка либо тело ошибки.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(
        map_set_episode_reaction_command(body, user_id=user.id, anime_id=anime_id)
    )
    if not result.ok:
        return error_from_result(result)
    return map_episode_reactions_response(result.data)
