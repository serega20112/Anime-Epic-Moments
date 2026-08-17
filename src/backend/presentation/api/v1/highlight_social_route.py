"""Highlight likes, saves and comments routes."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.application.use_cases import (
    AddHighlightCommentUseCase,
    GetHighlightLikersUseCase,
    SetHighlightLikeUseCase,
    SetSavedHighlightUseCase,
)
from backend.application.use_cases.highlight.get_highlight_comments import (
    GetHighlightCommentsUseCase,
)
from backend.infrastructure.security.flask_protection import client_ip, rate_limit
from backend.presentation.api.helpers import get_current_user, read_payload
from backend.presentation.api.requests.highlight_mapper import (
    map_add_comment_command,
    map_set_like_command,
    map_set_saved_command,
)
from backend.presentation.api.v1.highlight_route_helpers import read_limit

highlight_social_router = APIRouter(route_class=DishkaRoute)


async def _highlight_subject(request: Request) -> str:
    """Build a composite rate-limit subject for highlight social actions."""
    ip = await client_ip(request)
    user_id = getattr(await get_current_user(request), "id", "guest")
    return f"{ip}::{user_id}"


@highlight_social_router.get("/{highlight_id}/likes", name="highlight.get_highlight_likes")
@highlight_social_router.post("/{highlight_id}/likes", name="highlight.highlight_likes")
@highlight_social_router.delete("/{highlight_id}/likes", name="highlight.remove_highlight_like")
@rate_limit(
    scope="highlight_like",
    limit=60,
    window_seconds=60,
    key_builder=_highlight_subject,
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
    user = await get_current_user(request)
    if not user:
        return JSONResponse(
            {"error": "auth_required"},
            status_code=HTTPStatus.UNAUTHORIZED,
        )
    command = await map_set_like_command(request, highlight_id=highlight_id, user_id=user.id)
    result = await set_like_use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return {
        "highlight_id": highlight_id,
        "liked": command.liked,
        "likes_count": getattr(result.data, "likes_count", 0),
    }


@highlight_social_router.post("/{highlight_id}/save", name="highlight.set_saved_highlight")
@highlight_social_router.delete("/{highlight_id}/save", name="highlight.unset_saved_highlight")
@rate_limit(
    scope="highlight_save",
    limit=60,
    window_seconds=60,
    key_builder=_highlight_subject,
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
    user = await get_current_user(request)
    if not user:
        return JSONResponse(
            {"error": "auth_required"},
            status_code=HTTPStatus.UNAUTHORIZED,
        )
    command = await map_set_saved_command(request, highlight_id=highlight_id, user_id=user.id)
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return {"highlight_id": highlight_id, "saved": result.data}


@highlight_social_router.get("/{highlight_id}/comments", name="highlight.get_highlight_comments")
@highlight_social_router.post("/{highlight_id}/comments", name="highlight.highlight_comments")
@rate_limit(
    scope="highlight_comment",
    limit=30,
    window_seconds=60,
    key_builder=_highlight_subject,
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
        limit = await read_limit(request, default=20, maximum=100)
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
    user = await get_current_user(request)
    if not user:
        return JSONResponse(
            {"error": "auth_required"},
            status_code=HTTPStatus.UNAUTHORIZED,
        )
    payload = await read_payload(request)
    command = await map_add_comment_command(payload, highlight_id=highlight_id, user_id=user.id)
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
    limit = await read_limit(request, default=20, maximum=100)
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
