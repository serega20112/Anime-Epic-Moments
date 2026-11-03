"""Страничные маршруты хайлайтов: ленты, списки, шеринг и уведомления."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.dto import HighlightNotificationsQuery, HighlightSharedQuery
from backend.application.use_cases import (
    GetFollowingHighlightsUseCase,
    GetHighlightFeedUseCase,
    GetHighlightNotificationsUseCase,
    GetLikedHighlightsUseCase,
    GetPublicTopHighlightsUseCase,
    GetSavedHighlightsUseCase,
    GetSharedHighlightUseCase,
    GetUserHighlightsUseCase,
)
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.highlight_mapper import map_dashboard_query, map_feed_query
from backend.presentation.api.v1.highlights.helpers import read_limit, redirect_login
from backend.presentation.web import render_template

highlight_pages_router = APIRouter(route_class=DishkaRoute)


@highlight_pages_router.get("/feed", name="highlight.get_highlight_feed")
async def get_highlight_feed(
    request: Request,
    use_case: FromDishka[GetHighlightFeedUseCase],
):
    """Отдать страницу ленты хайлайтов с фильтрами.

    Args:
        request: Текущий HTTP-запрос.
        use_case: Сценарий общей ленты хайлайтов.

    Returns:
        Response: Отрисованная страница ленты.
    """
    viewer = await get_current_user(request)
    query = map_feed_query(request, viewer_user_id=viewer.id if viewer else None)
    feed = await use_case.execute(query)
    return await render_template(request, "highlight/feed.html", feed=feed)


@highlight_pages_router.get("/following", name="highlight.get_following_highlights")
async def get_following_highlights(
    request: Request,
    use_case: FromDishka[GetFollowingHighlightsUseCase],
):
    """Отдать хайлайты пользователей из подписок зрителя.

    Args:
        request: Текущий HTTP-запрос.
        use_case: Сценарий ленты хайлайтов подписок.

    Returns:
        Response: Страница подписок либо редирект на вход.
    """
    user = await get_current_user(request)
    if not user:
        return redirect_login(request)
    query = map_dashboard_query(request, user_id=user.id, viewer_user_id=user.id)
    page = await use_case.execute(query)
    return await render_template(request, "highlight/following.html", page=page)


@highlight_pages_router.get("/saved", name="highlight.get_saved_highlights")
async def get_saved_highlights(
    request: Request,
    use_case: FromDishka[GetSavedHighlightsUseCase],
):
    """Отдать сохранённые пользователем хайлайты.

    Args:
        request: Текущий HTTP-запрос.
        use_case: Сценарий сохранённых хайлайтов.

    Returns:
        Response: Страница сохранённых либо редирект на вход.
    """
    user = await get_current_user(request)
    if not user:
        return redirect_login(request)
    query = map_dashboard_query(
        request,
        user_id=user.id,
        viewer_user_id=user.id,
        include_spoilers_default=True,
    )
    dashboard = await use_case.execute(query)
    return await render_template(
        request,
        "highlight/list.html",
        dashboard=dashboard,
        user_id=user.id,
        is_public=False,
        view_mode="saved",
    )


@highlight_pages_router.get("/liked", name="highlight.get_liked_highlights")
async def get_liked_highlights(
    request: Request,
    use_case: FromDishka[GetLikedHighlightsUseCase],
):
    """Отдать хайлайты, лайкнутые пользователем.

    Args:
        request: Текущий HTTP-запрос.
        use_case: Сценарий лайкнутых хайлайтов.

    Returns:
        Response: Страница лайкнутых либо редирект на вход.
    """
    user = await get_current_user(request)
    if not user:
        return redirect_login(request)
    query = map_dashboard_query(
        request,
        user_id=user.id,
        viewer_user_id=user.id,
        include_spoilers_default=True,
    )
    dashboard = await use_case.execute(query)
    return await render_template(
        request,
        "highlight/list.html",
        dashboard=dashboard,
        user_id=user.id,
        is_public=False,
        view_mode="liked",
    )


@highlight_pages_router.get("/share/{highlight_id}", name="highlight.get_shared_highlight")
async def get_shared_highlight(
    request: Request,
    highlight_id: int,
    use_case: FromDishka[GetSharedHighlightUseCase],
):
    """Отдать один хайлайт по публичной ссылке.

    Args:
        request: Текущий HTTP-запрос.
        highlight_id: Идентификатор хайлайта из пути.
        use_case: Сценарий публичной карточки хайлайта.

    Returns:
        Response: Страница хайлайта либо модальное окно 404.
    """
    viewer = await get_current_user(request)
    result = await use_case.execute(
        HighlightSharedQuery(
            highlight_id=highlight_id, viewer_user_id=viewer.id if viewer else None
        )
    )
    if not result.ok:
        return await render_template(
            request,
            "errors/500_modal.html",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return await render_template(
        request,
        "highlight/list.html",
        dashboard=result.data,
        user_id=None,
        is_public=True,
        view_mode="share",
    )


@highlight_pages_router.get("/notifications", name="highlight.get_highlight_notifications")
async def get_highlight_notifications(
    request: Request,
    use_case: FromDishka[GetHighlightNotificationsUseCase],
):
    """Отдать уведомления по хайлайтам пользователя.

    Args:
        request: Текущий HTTP-запрос.
        use_case: Сценарий уведомлений по хайлайтам.

    Returns:
        Response: Страница уведомлений либо редирект на вход.
    """
    user = await get_current_user(request)
    if not user:
        return redirect_login(request)
    items = await use_case.execute(
        HighlightNotificationsQuery(user_id=user.id, limit=read_limit(request, default=20))
    )
    return await render_template(request, "highlight/notifications.html", items=items)


@highlight_pages_router.get("/top", name="highlight.get_public_top_highlights")
async def get_public_top_highlights(
    request: Request,
    use_case: FromDishka[GetPublicTopHighlightsUseCase],
):
    """Отдать сводку популярных публичных хайлайтов.

    Args:
        request: Текущий HTTP-запрос.
        use_case: Сценарий публичного топа хайлайтов.

    Returns:
        Response: Страница публичного топа.
    """
    viewer = await get_current_user(request)
    query = map_dashboard_query(request, viewer_user_id=viewer.id if viewer else None)
    dashboard = await use_case.execute(query)
    return await render_template(
        request,
        "highlight/list.html",
        dashboard=dashboard,
        user_id=None,
        is_public=True,
        view_mode="public",
    )


@highlight_pages_router.get("/{user_id}", name="highlight.get_user_highlights")
async def get_user_highlights(
    request: Request,
    user_id: int,
    use_case: FromDishka[GetUserHighlightsUseCase],
):
    """Отдать хайлайты конкретного пользователя.

    Args:
        request: Текущий HTTP-запрос.
        user_id: Идентификатор автора хайлайтов из пути.
        use_case: Сценарий личного дашборда хайлайтов.

    Returns:
        Response: Страница хайлайтов пользователя.
    """
    viewer = await get_current_user(request)
    query = map_dashboard_query(
        request,
        user_id=user_id,
        viewer_user_id=viewer.id if viewer else None,
    )
    dashboard = await use_case.execute(query)
    return await render_template(
        request,
        "highlight/list.html",
        dashboard=dashboard,
        user_id=user_id,
        is_public=False,
        view_mode="user",
    )
