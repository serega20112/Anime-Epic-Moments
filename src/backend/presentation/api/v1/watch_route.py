"""Thin HTTP routes for the anime watch page and related player actions."""

from __future__ import annotations

import logging

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from backend.application.use_cases import (
    AddAnimeCommentUseCase,
    GetAnimeDiscussionUseCase,
    SetAnimeCommentLikeUseCase,
    SyncWatchSourcesUseCase,
    UpsertUserAnimeStatusUseCase,
)
from backend.application.use_cases.watch.create_watch_highlight import CreateWatchHighlightUseCase
from backend.application.use_cases.watch.get_watch_page import GetWatchPageUseCase
from backend.application.use_cases.watch.save_viewing_session import SaveViewingSessionUseCase
from backend.infrastructure.media_proxy import MediaProxyClient
from backend.infrastructure.security.flask_protection import client_ip, rate_limit
from backend.infrastructure.security.rate_limit_keys import (
    watch_anime_subject,
    watch_user_subject,
)
from backend.infrastructure.web import render_template
from backend.presentation.api.helpers import get_current_user, read_payload
from backend.presentation.api.redirects.watch import discussion_redirect
from backend.presentation.api.requests.watch_mapper import (
    _to_int,
    map_add_anime_comment_command,
    map_create_watch_highlight_command,
    map_save_session_command,
    map_set_comment_like_command,
    map_upsert_status_command,
    map_watch_page_query,
)

watch_router = APIRouter(prefix="/watch", route_class=DishkaRoute)
watch_bp = watch_router
logger = logging.getLogger("anime_epic_moments")


@watch_router.get("/proxy", name="watch.proxy_stream")
@watch_router.head("/proxy", name="watch.proxy_stream_head")
async def proxy_stream(
    request: Request,
    media_proxy_client: FromDishka[MediaProxyClient],
):
    """Proxy media streams with URL allowlist and HLS rewriting.

    Args:
        request: Incoming HTTP request with the target URL query param.
        media_proxy_client: Media proxy client.

    Returns:
        Response: Proxied media or an error response.
    """
    upstream_url = str(request.query_params.get("url") or "").strip()
    if not upstream_url:
        return Response(status_code=400)

    def proxy_url_builder(absolute_url: str) -> str:
        return f"{request.app.url_path_for('watch.proxy_stream')}?url={absolute_url}"

    return await media_proxy_client.proxy(
        request,
        upstream_url=upstream_url,
        proxy_url_builder=proxy_url_builder,
    )


@watch_router.get("/{anime_id}", name="watch.watch_page")
async def watch_page(
    request: Request,
    anime_id: int,
    watch_use_case: FromDishka[GetWatchPageUseCase],
    discussion_use_case: FromDishka[GetAnimeDiscussionUseCase],
):
    """Render the anime watch page.

    Args:
        request: Incoming HTTP request with query params.
        anime_id: Anime ID from path.
        watch_use_case: Get watch page use case.
        discussion_use_case: Get anime discussion use case.

    Returns:
        HTMLResponse: Rendered watch page template.
    """
    user = get_current_user(request)
    query = map_watch_page_query(request)
    data = await watch_use_case.execute(
        anime_id=anime_id,
        query=query,
        user_id=user.id if user else None,
    )
    discussion_result = await discussion_use_case.execute(
        anime_id=anime_id,
        sort_by=query.discussion_sort,
        viewer_user_id=user.id if user else None,
        limit=20,
    )
    discussion = discussion_result.data
    return render_template(request, "anime/watch.html", watch=data, discussion=discussion)


@watch_router.post("/{anime_id}/status", name="watch.update_status")
async def update_status(
    request: Request,
    anime_id: int,
    use_case: FromDishka[UpsertUserAnimeStatusUseCase],
):
    """Update the user's watch status for an anime.

    Args:
        request: Incoming HTTP request with JSON payload.
        anime_id: Anime ID from path.
        use_case: Upsert user anime status use case.

    Returns:
        JSONResponse: Updated status or an error.
    """
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    command = map_upsert_status_command(
        await read_payload(request),
        user_id=user.id,
        anime_id=anime_id,
    )
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return {"status": result.data.status}


@watch_router.post("/{anime_id}/sources", name="watch.add_source")
async def add_source(_request: Request, anime_id: int):
    """Manually add a watch source.

    Manual source creation is disabled.

    Args:
        _request: Incoming HTTP request.
        anime_id: Anime ID from path.

    Returns:
        JSONResponse: Disabled error response.
    """
    return JSONResponse({"error": "manual_source_creation_disabled"}, status_code=403)


@watch_router.post("/{anime_id}/sources/discover", name="watch.discover_sources")
@rate_limit(
    scope="watch_discover_sources",
    limit=15,
    window_seconds=60,
    key_builder=lambda request: watch_anime_subject(
        ip_address=client_ip(request),
        anime_id=request.path_params.get("anime_id"),
    ),
)
async def discover_sources(
    request: Request,
    anime_id: int,
    use_case: FromDishka[SyncWatchSourcesUseCase],
):
    """Discover watch sources from the external provider.

    Args:
        request: Incoming HTTP request with JSON payload.
        anime_id: Anime ID from path.
        use_case: Sync watch sources use case.

    Returns:
        JSONResponse: Sources payload or an error.
    """
    payload = await read_payload(request)
    episode = _to_int(str(payload.get("episode") or "")) or 1
    result = await use_case.execute(
        anime_id=anime_id,
        episode=episode,
        force=True,
    )
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return result.data


@watch_router.post("/{anime_id}/session", name="watch.save_session")
async def save_session(
    request: Request,
    anime_id: int,
    use_case: FromDishka[SaveViewingSessionUseCase],
):
    """Save the user's viewing session position.

    Args:
        request: Incoming HTTP request with JSON payload.
        anime_id: Anime ID from path.
        use_case: Save viewing session use case.

    Returns:
        JSONResponse: Session ID or an error.
    """
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    command = map_save_session_command(
        await read_payload(request),
        user_id=user.id,
        anime_id=anime_id,
    )
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return {"session_id": result.data.id}


@watch_router.post("/{anime_id}/highlights", name="watch.create_highlight")
@rate_limit(
    scope="watch_create_highlight",
    limit=20,
    window_seconds=60,
    key_builder=lambda request: watch_user_subject(
        ip_address=client_ip(request),
        user_id=getattr(get_current_user(request), "id", None),
    ),
)
async def create_highlight(
    request: Request,
    anime_id: int,
    use_case: FromDishka[CreateWatchHighlightUseCase],
):
    """Create a highlight from the player.

    Args:
        request: Incoming HTTP request with JSON payload.
        anime_id: Anime ID from path.
        use_case: Create watch highlight use case.

    Returns:
        JSONResponse: Highlight ID or an error.
    """
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    command = map_create_watch_highlight_command(
        await read_payload(request),
        user_id=user.id,
        anime_id=anime_id,
    )
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return JSONResponse({"highlight_id": result.data.id}, status_code=result.status_code)


@watch_router.post("/{anime_id}/discussion", name="watch.add_anime_comment")
async def add_anime_comment(
    request: Request,
    anime_id: int,
    use_case: FromDishka[AddAnimeCommentUseCase],
):
    """Add a comment to the anime discussion.

    Args:
        request: Incoming HTTP request with JSON payload.
        anime_id: Anime ID from path.
        use_case: Add anime comment use case.

    Returns:
        JSONResponse: Created comment or an error.
        RedirectResponse: Redirect for non-JSON clients.
    """
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    payload = await read_payload(request)
    command = map_add_anime_comment_command(
        payload,
        anime_id=anime_id,
        user_id=user.id,
    )
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    if _wants_json(request):
        return JSONResponse(vars(result.data), status_code=result.status_code)
    return discussion_redirect(request, anime_id, payload)


@watch_router.post("/discussion/comments/{comment_id}/likes", name="watch.set_anime_comment_like")
@watch_router.delete(
    "/discussion/comments/{comment_id}/likes", name="watch.remove_anime_comment_like"
)
async def set_anime_comment_like(
    request: Request,
    comment_id: int,
    use_case: FromDishka[SetAnimeCommentLikeUseCase],
):
    """Set or remove a like on a discussion comment.

    Args:
        request: Incoming HTTP request.
        comment_id: Comment ID from path.
        use_case: Set anime comment like use case.

    Returns:
        JSONResponse: Updated comment or an error.
    """
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    command = map_set_comment_like_command(
        request,
        comment_id=comment_id,
        user_id=user.id,
    )
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return vars(result.data)


@watch_router.get("/open/{anime_id}", name="watch.redirect_to_watch")
async def redirect_to_watch(request: Request, anime_id: int):
    """Redirect to the watch page for an anime.

    Args:
        request: Incoming HTTP request with query params.
        anime_id: Anime ID from path.

    Returns:
        RedirectResponse: SEE_OTHER redirect to the watch page.
    """
    episode = map_watch_page_query(request).episode
    url = request.app.url_path_for("watch.watch_page", anime_id=str(anime_id))
    return RedirectResponse(
        url=f"{url}?episode={episode}",
        status_code=303,
    )


def _wants_json(request: Request) -> bool:
    """Determine if the client expects a JSON response.

    Args:
        request: Incoming HTTP request.

    Returns:
        bool: True if the request content type is JSON.
    """
    return "application/json" in str(request.headers.get("content-type") or "").lower()
