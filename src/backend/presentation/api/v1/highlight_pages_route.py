"""Page-rendering highlight routes: feeds, lists, sharing, and notifications."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

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
from backend.infrastructure.web import render_template
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.highlight_mapper import (
    map_dashboard_query,
    map_feed_query,
    map_list_query,
)
from backend.presentation.api.v1.highlight_route_helpers import read_limit, redirect_login

highlight_pages_router = APIRouter(route_class=DishkaRoute)


@highlight_pages_router.get("/feed", name="highlight.get_highlight_feed")
async def get_highlight_feed(
    request: Request,
    use_case: FromDishka[GetHighlightFeedUseCase],
):
    """Render the highlight feed page with optional filters.

    Args:
        request: Incoming HTTP request with query params.
        use_case: Get highlight feed use case.

    Returns:
        HTMLResponse: Rendered feed template.
    """
    viewer = await get_current_user(request)
    query = await map_feed_query(request, viewer_user_id=viewer.id if viewer else None)
    feed = await use_case.execute(
        viewer_user_id=query.viewer_user_id,
        anime_id=query.anime_id,
        category=query.category,
        include_spoilers=query.include_spoilers,
        limit=query.limit,
    )
    return await render_template(request, "highlight/feed.html", feed=feed)


@highlight_pages_router.get("/following", name="highlight.get_following_highlights")
async def get_following_highlights(
    request: Request,
    use_case: FromDishka[GetFollowingHighlightsUseCase],
):
    """Render highlights from users the current user follows.

    Args:
        request: Incoming HTTP request with query params.
        use_case: Get following highlights use case.

    Returns:
        RedirectResponse: Login redirect for guests.
        HTMLResponse: Rendered following highlights template.
    """
    user = await get_current_user(request)
    if not user:
        return await redirect_login(request)
    query = await map_dashboard_query(request, viewer_user_id=user.id)
    page = await use_case.execute(
        follower_user_id=user.id,
        anime_id=query.anime_id,
        emotion=query.emotion,
        category=query.category,
        sort_by=query.sort_by,
        created_date=query.created_date,
        query=query.query,
        include_spoilers=query.include_spoilers,
        limit=query.limit,
    )
    return await render_template(request, "highlight/following.html", page=page)


@highlight_pages_router.get("/saved", name="highlight.get_saved_highlights")
async def get_saved_highlights(
    request: Request,
    use_case: FromDishka[GetSavedHighlightsUseCase],
):
    """Render highlights saved by the current user.

    Args:
        request: Incoming HTTP request with query params.
        use_case: Get saved highlights use case.

    Returns:
        RedirectResponse: Login redirect for guests.
        HTMLResponse: Rendered saved highlights template.
    """
    user = await get_current_user(request)
    if not user:
        return await redirect_login(request)
    query = await map_list_query(request, include_spoilers_default=True)
    dashboard = await use_case.execute(
        user_id=user.id,
        anime_id=query.anime_id,
        emotion=query.emotion,
        category=query.category,
        sort_by=query.sort_by,
        created_date=query.created_date,
        query=query.query,
        include_spoilers=query.include_spoilers,
    )
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
    """Render highlights liked by the current user.

    Args:
        request: Incoming HTTP request with query params.
        use_case: Get liked highlights use case.

    Returns:
        RedirectResponse: Login redirect for guests.
        HTMLResponse: Rendered liked highlights template.
    """
    user = await get_current_user(request)
    if not user:
        return await redirect_login(request)
    query = await map_list_query(request, include_spoilers_default=True)
    dashboard = await use_case.execute(
        user_id=user.id,
        anime_id=query.anime_id,
        emotion=query.emotion,
        category=query.category,
        sort_by=query.sort_by,
        created_date=query.created_date,
        query=query.query,
        include_spoilers=query.include_spoilers,
    )
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
    """Render a single highlight for public sharing.

    Args:
        request: Incoming HTTP request.
        highlight_id: Highlight ID from path.
        use_case: Get shared highlight use case.

    Returns:
        HTMLResponse: Rendered shared highlight template or 404 modal.
    """
    viewer = await get_current_user(request)
    result = await use_case.execute(
        highlight_id=highlight_id,
        viewer_user_id=viewer.id if viewer else None,
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
    """Render highlight notifications for the current user.

    Args:
        request: Incoming HTTP request.
        use_case: Get highlight notifications use case.

    Returns:
        RedirectResponse: Login redirect for guests.
        HTMLResponse: Rendered notifications template.
    """
    user = await get_current_user(request)
    if not user:
        return await redirect_login(request)
    limit = await read_limit(request, default=20, maximum=100)
    items = await use_case.execute(
        user_id=user.id,
        limit=limit,
    )
    return await render_template(request, "highlight/notifications.html", items=items)


@highlight_pages_router.get("/top", name="highlight.get_public_top_highlights")
async def get_public_top_highlights(
    request: Request,
    use_case: FromDishka[GetPublicTopHighlightsUseCase],
):
    """Render the public top highlights dashboard.

    Args:
        request: Incoming HTTP request with query params.
        use_case: Get public top highlights use case.

    Returns:
        HTMLResponse: Rendered top highlights template.
    """
    viewer = await get_current_user(request)
    query = await map_dashboard_query(request, viewer_user_id=viewer.id if viewer else None)
    dashboard = await use_case.execute(
        limit=query.limit,
        anime_id=query.anime_id,
        emotion=query.emotion,
        category=query.category,
        sort_by=query.sort_by,
        created_date=query.created_date,
        query=query.query,
        include_spoilers=query.include_spoilers,
        viewer_user_id=query.viewer_user_id,
    )
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
    """Render highlights created by a specific user.

    Args:
        request: Incoming HTTP request with query params.
        user_id: User ID from path.
        use_case: Get user highlights use case.

    Returns:
        HTMLResponse: Rendered user highlights template.
    """
    viewer = await get_current_user(request)
    query = await map_dashboard_query(request, viewer_user_id=viewer.id if viewer else None)
    dashboard = await use_case.execute(
        user_id=user_id,
        anime_id=query.anime_id,
        emotion=query.emotion,
        category=query.category,
        sort_by=query.sort_by,
        created_date=query.created_date,
        query=query.query,
        include_spoilers=query.include_spoilers,
        viewer_user_id=query.viewer_user_id,
    )
    return await render_template(
        request,
        "highlight/list.html",
        dashboard=dashboard,
        user_id=user_id,
        is_public=False,
        view_mode="user",
    )
