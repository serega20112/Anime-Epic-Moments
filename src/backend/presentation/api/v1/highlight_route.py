"""Thin HTTP routes for highlight management: create, edit, delete, feed, likes, comments, saves."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from backend.application.use_cases import AddHighlightCommentUseCase
from backend.application.use_cases import DeleteHighlightUseCase
from backend.application.use_cases import EditHighlightUseCase
from backend.application.use_cases import GetFollowingHighlightsUseCase
from backend.application.use_cases import GetHighlightFeedUseCase
from backend.application.use_cases import GetHighlightLikersUseCase
from backend.application.use_cases import GetHighlightNotificationsUseCase
from backend.application.use_cases import GetLikedHighlightsUseCase
from backend.application.use_cases import GetPublicTopHighlightsUseCase
from backend.application.use_cases import GetSavedHighlightsUseCase
from backend.application.use_cases import GetSharedHighlightUseCase
from backend.application.use_cases import GetUserHighlightsUseCase
from backend.application.use_cases import SetHighlightLikeUseCase
from backend.application.use_cases import SetSavedHighlightUseCase
from backend.application.use_cases.highlight.create_highlight import CreateHighlightUseCase
from backend.application.use_cases.highlight.get_highlight_comments import (
    GetHighlightCommentsUseCase,
)
from backend.presentation.api.requests.highlight_mapper import (
    map_add_comment_command,
    map_create_highlight_command,
    map_dashboard_query,
    map_delete_highlight_command,
    map_edit_highlight_command,
    map_feed_query,
    map_list_query,
    map_set_like_command,
    map_set_saved_command,
)

from backend.infrastructure.security.flask_protection import client_ip, rate_limit
from backend.infrastructure.web import render_template
from backend.presentation.api.helpers import get_current_user, read_payload

highlight_router = APIRouter(prefix="/highlights", route_class=DishkaRoute)
highlight_bp = highlight_router


@highlight_router.post("/", name="highlight.create_highlight")
@rate_limit(
    scope="highlight_create",
    limit=20,
    window_seconds=60,
    key_builder=lambda request: (
            f"{client_ip(request)}::{getattr(get_current_user(request), 'id', 'guest')}"
    ),
)
async def create_highlight(
        request: Request,
        use_case: FromDishka[CreateHighlightUseCase],
):
    """Create a new highlight from JSON payload.

    Args:
        request: Incoming HTTP request with highlight data.
        use_case: Create highlight use case.

    Returns:
        JSONResponse: Created highlight ID with 201 status or an error.
    """
    payload = await read_payload(request)
    user = get_current_user(request)
    command = map_create_highlight_command(payload, user_id=user.id if user else None)
    if command is None:
        return JSONResponse(
            {"error": "invalid_payload"},
            status_code=HTTPStatus.BAD_REQUEST,
        )
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return JSONResponse(
        {"highlight_id": getattr(result.data, "id", None)},
        status_code=result.status_code,
    )


@highlight_router.get("/feed", name="highlight.get_highlight_feed")
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
    viewer = get_current_user(request)
    query = map_feed_query(request, viewer_user_id=viewer.id if viewer else None)
    feed = await use_case.execute(
        viewer_user_id=query.viewer_user_id,
        anime_id=query.anime_id,
        category=query.category,
        include_spoilers=query.include_spoilers,
        limit=query.limit,
    )
    return render_template(request, "highlight/feed.html", feed=feed)


@highlight_router.get("/following", name="highlight.get_following_highlights")
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
    user = get_current_user(request)
    if not user:
        return _redirect_login(request)
    query = map_dashboard_query(request, viewer_user_id=user.id)
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
    return render_template(request, "highlight/following.html", page=page)


@highlight_router.get("/saved", name="highlight.get_saved_highlights")
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
    user = get_current_user(request)
    if not user:
        return _redirect_login(request)
    query = map_list_query(request, include_spoilers_default=True)
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
    return render_template(
        request,
        "highlight/list.html",
        dashboard=dashboard,
        user_id=user.id,
        is_public=False,
        view_mode="saved",
    )


@highlight_router.get("/liked", name="highlight.get_liked_highlights")
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
    user = get_current_user(request)
    if not user:
        return _redirect_login(request)
    query = map_list_query(request, include_spoilers_default=True)
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
    return render_template(
        request,
        "highlight/list.html",
        dashboard=dashboard,
        user_id=user.id,
        is_public=False,
        view_mode="liked",
    )


@highlight_router.get("/share/{highlight_id}", name="highlight.get_shared_highlight")
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
    viewer = get_current_user(request)
    result = await use_case.execute(
        highlight_id=highlight_id,
        viewer_user_id=viewer.id if viewer else None,
    )
    if not result.ok:
        return render_template(
            request,
            "errors/500_modal.html",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return render_template(
        request,
        "highlight/list.html",
        dashboard=result.data,
        user_id=None,
        is_public=True,
        view_mode="share",
    )


@highlight_router.get("/notifications", name="highlight.get_highlight_notifications")
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
    user = get_current_user(request)
    if not user:
        return _redirect_login(request)
    limit = _read_limit(request, default=20, maximum=100)
    items = await use_case.execute(
        user_id=user.id,
        limit=limit,
    )
    return render_template(request, "highlight/notifications.html", items=items)


@highlight_router.get("/top", name="highlight.get_public_top_highlights")
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
    viewer = get_current_user(request)
    query = map_dashboard_query(request, viewer_user_id=viewer.id if viewer else None)
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
    return render_template(
        request,
        "highlight/list.html",
        dashboard=dashboard,
        user_id=None,
        is_public=True,
        view_mode="public",
    )


@highlight_router.get("/{user_id}", name="highlight.get_user_highlights")
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
    viewer = get_current_user(request)
    query = map_dashboard_query(request, viewer_user_id=viewer.id if viewer else None)
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
    return render_template(
        request,
        "highlight/list.html",
        dashboard=dashboard,
        user_id=user_id,
        is_public=False,
        view_mode="user",
    )


@highlight_router.put("/{highlight_id}", name="highlight.edit_highlight")
async def edit_highlight(
        request: Request,
        highlight_id: int,
        use_case: FromDishka[EditHighlightUseCase],
):
    """Edit an existing highlight.

    Args:
        request: Incoming HTTP request with updated data.
        highlight_id: Highlight ID from path.
        use_case: Edit highlight use case.

    Returns:
        JSONResponse: 204 on success or an error.
    """
    payload = await read_payload(request)
    command = map_edit_highlight_command(payload, highlight_id=highlight_id)
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return Response(status_code=result.status_code)


@highlight_router.delete("/{highlight_id}", name="highlight.delete_highlight")
async def delete_highlight(
        request: Request,
        highlight_id: int,
        use_case: FromDishka[DeleteHighlightUseCase],
):
    """Delete a highlight.

    Args:
        request: Incoming HTTP request.
        highlight_id: Highlight ID from path.
        use_case: Delete highlight use case.

    Returns:
        JSONResponse: 204 on success or an error.
    """
    command = map_delete_highlight_command(highlight_id=highlight_id)
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return Response(status_code=result.status_code)


@highlight_router.get("/{highlight_id}/likes", name="highlight.get_highlight_likes")
@highlight_router.post("/{highlight_id}/likes", name="highlight.highlight_likes")
@highlight_router.delete("/{highlight_id}/likes", name="highlight.remove_highlight_like")
@rate_limit(
    scope="highlight_like",
    limit=60,
    window_seconds=60,
    key_builder=lambda request: (
            f"{client_ip(request)}::{getattr(get_current_user(request), 'id', 'guest')}"
    ),
)
async def highlight_likes(
        request: Request,
        highlight_id: int,
        set_like_use_case: FromDishka[SetHighlightLikeUseCase],
        get_likers_use_case: FromDishka[GetHighlightLikersUseCase],
):
    """Get, set, or remove a highlight like.

    GET returns likers list, POST adds a like, DELETE removes it.

    Args:
        request: Incoming HTTP request.
        highlight_id: Highlight ID from path.
        set_like_use_case: Set highlight like use case.
        get_likers_use_case: Get highlight likers use case.

    Returns:
        JSONResponse: Like operation result.
    """
    if request.method == "GET":
        return await _get_likers(request, highlight_id, get_likers_use_case)
    user = get_current_user(request)
    if not user:
        return JSONResponse(
            {"error": "auth_required"},
            status_code=HTTPStatus.UNAUTHORIZED,
        )
    command = map_set_like_command(request, highlight_id=highlight_id, user_id=user.id)
    result = await set_like_use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return {
        "highlight_id": highlight_id,
        "liked": command.liked,
        "likes_count": getattr(result.data, "likes_count", 0),
    }


@highlight_router.post("/{highlight_id}/save", name="highlight.set_saved_highlight")
@highlight_router.delete("/{highlight_id}/save", name="highlight.unset_saved_highlight")
@rate_limit(
    scope="highlight_save",
    limit=60,
    window_seconds=60,
    key_builder=lambda request: (
            f"{client_ip(request)}::{getattr(get_current_user(request), 'id', 'guest')}"
    ),
)
async def set_saved_highlight(
        request: Request,
        highlight_id: int,
        use_case: FromDishka[SetSavedHighlightUseCase],
):
    """Save or unsave a highlight.

    POST saves, DELETE removes from saved.

    Args:
        request: Incoming HTTP request.
        highlight_id: Highlight ID from path.
        use_case: Set saved highlight use case.

    Returns:
        JSONResponse: Save operation result.
    """
    user = get_current_user(request)
    if not user:
        return JSONResponse(
            {"error": "auth_required"},
            status_code=HTTPStatus.UNAUTHORIZED,
        )
    command = map_set_saved_command(request, highlight_id=highlight_id, user_id=user.id)
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return {"highlight_id": highlight_id, "saved": result.data}


@highlight_router.get("/{highlight_id}/comments", name="highlight.get_highlight_comments")
@highlight_router.post("/{highlight_id}/comments", name="highlight.highlight_comments")
@rate_limit(
    scope="highlight_comment",
    limit=30,
    window_seconds=60,
    key_builder=lambda request: (
            f"{client_ip(request)}::{getattr(get_current_user(request), 'id', 'guest')}"
    ),
)
async def highlight_comments(
        request: Request,
        highlight_id: int,
        get_comments_use_case: FromDishka[GetHighlightCommentsUseCase],
        add_comment_use_case: FromDishka[AddHighlightCommentUseCase],
):
    """Get or add highlight comments.

    GET returns comments list, POST adds a new comment.

    Args:
        request: Incoming HTTP request.
        highlight_id: Highlight ID from path.
        get_comments_use_case: Get highlight comments use case.
        add_comment_use_case: Add highlight comment use case.

    Returns:
        JSONResponse: Comment operation result.
    """
    if request.method == "GET":
        limit = _read_limit(request, default=20, maximum=100)
        items = await get_comments_use_case.execute(
            highlight_id=highlight_id,
            limit=limit,
        )
        return {
            "items": [
                {
                    "id": item.id,
                    "user_id": item.user_id,
                    "username": item.username,
                    "content": item.content,
                    "created_at": item.created_at,
                }
                for item in items
            ]
        }
    user = get_current_user(request)
    if not user:
        return JSONResponse(
            {"error": "auth_required"},
            status_code=HTTPStatus.UNAUTHORIZED,
        )
    payload = await read_payload(request)
    command = map_add_comment_command(payload, highlight_id=highlight_id, user_id=user.id)
    result = await add_comment_use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    comment = result.data
    return JSONResponse(
        {
            "id": comment.id,
            "user_id": comment.user_id,
            "username": comment.username,
            "content": comment.content,
            "created_at": comment.created_at,
        },
        status_code=result.status_code,
    )


async def _get_likers(
        request: Request,
        highlight_id: int,
        use_case: GetHighlightLikersUseCase,
):
    """Return the likers list for a highlight.

    Args:
        request: Incoming HTTP request.
        highlight_id: Highlight ID from path.
        use_case: Get highlight likers use case.

    Returns:
        dict: Likers payload.
    """
    limit = _read_limit(request, default=20, maximum=100)
    items = await use_case.execute(
        highlight_id=highlight_id,
        limit=limit,
    )
    return {
        "items": [
            {
                "user_id": item.user_id,
                "username": item.username,
                "created_at": item.created_at,
            }
            for item in items
        ]
    }


def _read_limit(request: Request, *, default: int, maximum: int) -> int:
    """Parse and clamp a limit query parameter.

    Args:
        request: Incoming HTTP request.
        default: Default value when missing or invalid.
        maximum: Maximum allowed value.

    Returns:
        int: Clamped limit.
    """
    raw = request.query_params.get("limit")
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return default
    return max(min(parsed, maximum), 1)


def _redirect_login(request: Request) -> RedirectResponse:
    """Build a redirect to the login page.

    Args:
        request: Incoming HTTP request.

    Returns:
        RedirectResponse: SEE_OTHER redirect to login.
    """
    return RedirectResponse(
        url=request.app.url_path_for("auth.login_page"),
        status_code=HTTPStatus.SEE_OTHER,
    )
