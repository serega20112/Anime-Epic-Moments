"""Маршруты избранного: добавление, удаление и список."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from backend.application.dto import RecommendationsQuery
from backend.application.dto.favorite import (
    AddFavoriteCommand,
    GetFavoriteIdsQuery,
    GetFavoritesQuery,
    RemoveFavoriteCommand,
)
from backend.application.use_cases import (
    GenerateRecommendationsUseCase,
    GetFavoriteIdsUseCase,
    GetFavoritesUseCase,
)
from backend.application.use_cases.favorite.add_favorite import AddFavoriteUseCase
from backend.application.use_cases.favorite.remove_favorite import RemoveFavoriteUseCase
from backend.presentation.api.errors import ErrorResponse, unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.favorite_requests import (
    AddFavoriteRequest,
    RemoveFavoriteRequest,
)
from backend.presentation.api.responses.favorite_responses import FavoriteIdsResponse
from backend.presentation.dependencies.auth import require_self
from backend.presentation.web import render_template

favorite_router = APIRouter(prefix="/favorites", route_class=DishkaRoute)


@favorite_router.post(
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


@favorite_router.delete(
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


@favorite_router.get(
    "/ids/{user_id}",
    name="favorite.get_favorite_ids",
    response_model=FavoriteIdsResponse,
    responses={
        HTTPStatus.UNAUTHORIZED: {"model": ErrorResponse},
        HTTPStatus.FORBIDDEN: {"model": ErrorResponse},
    },
)
async def get_favorite_ids(
    user_id: int,
    use_case: FromDishka[GetFavoriteIdsUseCase],
    session_user_id: int = Depends(require_self),
):
    """Возвращает идентификаторы избранного пользователя в формате JSON.

    Избранное — приватные данные: идентификатор из пути сверяется с сессией,
    и только при совпадении сценарий получает его в работу.

    Args:
        user_id: Идентификатор пользователя из пути.
        use_case: Сценарий получения идентификаторов избранного.
        session_user_id: Идентификатор пользователя сессии.

    Returns:
        FavoriteIdsResponse: Идентификаторы избранного пользователя сессии.
    """
    anime_ids = await use_case.execute(GetFavoriteIdsQuery(user_id=session_user_id))
    return FavoriteIdsResponse(user_id=session_user_id, anime_ids=anime_ids)


@favorite_router.get("/{user_id}", name="favorite.get_favorites")
async def get_favorites(
    request: Request,
    user_id: int,
    favorites_use_case: FromDishka[GetFavoritesUseCase],
    recommendations_use_case: FromDishka[GenerateRecommendationsUseCase],
    session_user_id: int = Depends(require_self),
):
    """Рендерит страницу избранного с рекомендациями.

    Args:
        request: Текущий HTTP-запрос.
        user_id: Идентификатор пользователя из пути.
        favorites_use_case: Сценарий получения избранного.
        recommendations_use_case: Сценарий генерации рекомендаций.
        session_user_id: Идентификатор пользователя сессии.

    Returns:
        HTMLResponse: Отрисованный шаблон списка избранного.

    Raises:
        HTTPException: 401 для анонимного запроса, 403 при чужом ``user_id``.
    """
    favorites = await favorites_use_case.execute(GetFavoritesQuery(user_id=session_user_id))
    recommendations = await recommendations_use_case.execute(
        RecommendationsQuery(user_id=session_user_id)
    )
    return await render_template(
        request,
        "favorite/list.html",
        favorites=favorites,
        recommendations=recommendations,
        user_id=session_user_id,
    )
