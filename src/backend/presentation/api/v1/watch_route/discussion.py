"""Маршруты обсуждения аниме: комментарий и лайк к нему."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.use_cases import (
    AddAnimeCommentUseCase,
    SetAnimeCommentLikeUseCase,
)
from backend.presentation.api.errors import error_from_result, unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.watch_mapper import (
    map_add_anime_comment_command,
    map_set_comment_like_command,
)
from backend.presentation.api.requests.watch_requests import AddAnimeCommentRequest
from backend.presentation.api.responses.watch_responses import AnimeCommentResponse
from backend.presentation.api.v1.watch_route.helpers import ERROR_RESPONSES, comment_response

discussion_router = APIRouter(route_class=DishkaRoute)


@discussion_router.post(
    "/{anime_id}/discussion",
    name="watch.add_anime_comment",
    status_code=HTTPStatus.CREATED,
    response_model=AnimeCommentResponse,
    responses=ERROR_RESPONSES,
)
async def add_anime_comment(
    request: Request,
    anime_id: int,
    body: AddAnimeCommentRequest,
    use_case: FromDishka[AddAnimeCommentUseCase],
):
    """Добавить комментарий в обсуждение аниме.

    Args:
        request: Текущий HTTP-запрос.
        anime_id: Идентификатор аниме из пути.
        body: Проверенное тело комментария.
        use_case: Сценарий добавления комментария.

    Returns:
        AnimeCommentResponse: Созданный комментарий либо тело ошибки.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(
        map_add_anime_comment_command(body, anime_id=anime_id, user_id=user.id)
    )
    if not result.ok:
        return error_from_result(result)
    return comment_response(result.data)


@discussion_router.post(
    "/discussion/comments/{comment_id}/likes",
    name="watch.set_anime_comment_like",
    response_model=AnimeCommentResponse,
    responses=ERROR_RESPONSES,
)
@discussion_router.delete(
    "/discussion/comments/{comment_id}/likes",
    name="watch.remove_anime_comment_like",
    response_model=AnimeCommentResponse,
    responses=ERROR_RESPONSES,
)
async def set_anime_comment_like(
    request: Request,
    comment_id: int,
    use_case: FromDishka[SetAnimeCommentLikeUseCase],
):
    """Поставить или снять лайк комментария обсуждения.

    Args:
        request: Текущий HTTP-запрос.
        comment_id: Идентификатор комментария из пути.
        use_case: Сценарий лайка комментария.

    Returns:
        AnimeCommentResponse: Обновлённый комментарий либо тело ошибки.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(
        map_set_comment_like_command(
            comment_id=comment_id,
            user_id=user.id,
            liked=request.method != "DELETE",
        )
    )
    if not result.ok:
        return error_from_result(result)
    return comment_response(result.data)
