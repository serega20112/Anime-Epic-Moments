"""Маршруты изменения избранного: добавление и удаление аниме."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import Response

from backend.application.dto.favorite import AddFavoriteCommand, RemoveFavoriteCommand
from backend.application.use_cases.favorite.add_favorite import AddFavoriteUseCase
from backend.application.use_cases.favorite.remove_favorite import RemoveFavoriteUseCase
from backend.presentation.api.errors import ErrorResponse, unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.favorite_requests import (
    AddFavoriteRequest,
    RemoveFavoriteRequest,
)

favorite_ops_router = APIRouter(route_class=DishkaRoute)


@favorite_ops_router.post(
    "/",
    name="favorite.add_favorite",
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.CREATED: {"description": "Избранное сохранено, тело ответа пустое."},
        HTTPStatus.UNAUTHORIZED: {"model": ErrorResponse},
    },
)
async def add_favorite(
    request: Request,
    body: AddFavoriteRequest,
    use_case: FromDishka[AddFavoriteUseCase],
):
    """Добавляет аниме в избранное авторизованного пользователя.

    Args:
        request: Текущий HTTP-запрос.
        body: Тело запроса с данными аниме.
        use_case: Сценарий добавления в избранное.

    Returns:
        Response: 201 Created либо 401 без сессии.
    """
    user = await get_current_user(request)
    if user is None:
        return unauthorized_error()
    await use_case.execute(
        AddFavoriteCommand(
            user_id=user.id,
            anime_id=body.anime_id,
            title=body.title,
            description=body.description,
            cover_url=body.cover_url,
            genres=body.genres,
            original_title=body.original_title,
        )
    )
    return Response(status_code=HTTPStatus.CREATED)


@favorite_ops_router.delete(
    "/",
    name="favorite.remove_favorite",
    status_code=HTTPStatus.NO_CONTENT,
    responses={HTTPStatus.UNAUTHORIZED: {"model": ErrorResponse}},
)
async def remove_favorite(
    request: Request,
    body: RemoveFavoriteRequest,
    use_case: FromDishka[RemoveFavoriteUseCase],
):
    """Удаляет аниме из избранного авторизованного пользователя.

    Args:
        request: Текущий HTTP-запрос.
        body: Тело запроса с идентификатором аниме.
        use_case: Сценарий удаления из избранного.

    Returns:
        Response: 204 No Content либо 401 без сессии.
    """
    user = await get_current_user(request)
    if user is None:
        return unauthorized_error()
    await use_case.execute(RemoveFavoriteCommand(user_id=user.id, anime_id=body.anime_id))
    return Response(status_code=HTTPStatus.NO_CONTENT)
