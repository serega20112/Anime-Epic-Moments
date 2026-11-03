"""Маршруты чтения избранного: идентификаторы, карточки и страница."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends, Request

from backend.application.dto import RecommendationsQuery
from backend.application.dto.favorite import GetFavoriteIdsQuery, GetFavoritesQuery
from backend.application.use_cases import (
    GenerateRecommendationsUseCase,
    GetFavoriteIdsUseCase,
    GetFavoritesUseCase,
)
from backend.presentation.api.errors import ErrorResponse
from backend.presentation.api.responses.favorite_responses import (
    FavoriteAnimeCardResponse,
    FavoriteIdsResponse,
)
from backend.presentation.api.responses.pagination import Page, as_single_page
from backend.presentation.dependencies.auth import require_self
from backend.presentation.web import render_template

favorite_queries_router = APIRouter(route_class=DishkaRoute)


@favorite_queries_router.get(
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


@favorite_queries_router.get(
    "/cards/{user_id}",
    name="favorite.get_favorite_cards",
    response_model=Page[FavoriteAnimeCardResponse],
    responses={
        HTTPStatus.UNAUTHORIZED: {"model": ErrorResponse},
        HTTPStatus.FORBIDDEN: {"model": ErrorResponse},
    },
)
async def get_favorite_cards(
    user_id: int,
    use_case: FromDishka[GetFavoritesUseCase],
    session_user_id: int = Depends(require_self),
):
    """Возвращает карточки избранного пользователя в формате JSON.

    Избранное — приватные данные: идентификатор из пути сверяется с сессией.
    Список берётся целиком существующим сценарием и лишь оборачивается в
    единый конверт постраничной выдачи; нарезку на страницы сценарий
    избранного пока не поддерживает, поэтому вся выборка идёт одной страницей.

    Args:
        user_id: Идентификатор пользователя из пути.
        use_case: Сценарий получения карточек избранного.
        session_user_id: Идентификатор пользователя сессии.

    Returns:
        Page[FavoriteAnimeCardResponse]: Карточки избранного владельца сессии.

    Raises:
        HTTPException: 401 для анонимного запроса, 403 при чужом ``user_id``.
    """
    cards = await use_case.execute(GetFavoritesQuery(user_id=session_user_id))
    return Page(
        **as_single_page([FavoriteAnimeCardResponse.model_validate(card) for card in cards])
    )


@favorite_queries_router.get("/{user_id}", name="favorite.get_favorites")
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
