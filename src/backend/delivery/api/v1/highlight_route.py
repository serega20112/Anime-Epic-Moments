from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from src.backend.delivery.api.helpers import (
    get_container,
    get_current_user,
    read_payload,
)
from src.backend.infrastructure.security.flask_protection import client_ip, rate_limit
from src.backend.infrastructure.web.templating import render_template

highlight_router = APIRouter(prefix="/highlights")
highlight_bp = highlight_router
container = None


@highlight_router.post("/", name="highlight.create_highlight")
@rate_limit(
    scope="highlight_create",
    limit=20,
    window_seconds=60,
    key_builder=lambda request: f"{client_ip(request)}::{getattr(get_current_user(request), 'id', 'guest')}",
)
async def create_highlight(request: Request):
    container = get_container(request)
    data = await read_payload(request)
    anime_id = _to_int(data.get("anime_id"))
    episode = _to_int(data.get("episode"))
    start_timestamp = _safe_to_seconds(data.get("start_timestamp"))
    end_timestamp = _safe_to_seconds(data.get("end_timestamp"))
    if anime_id is None or episode is None or start_timestamp is None or end_timestamp is None:
        return JSONResponse({"error": "invalid_payload"}, status_code=400)
    highlight = await container.create_highlight_use_case().execute(
        user_id=_to_int(data.get("user_id")),
        anime_id=anime_id,
        episode=episode,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        title=str(data.get("title") or "").strip(),
        category=_normalize_optional_text(data.get("category")),
        description=str(data.get("description") or "").strip(),
        is_spoiler=_to_bool(str(data.get("is_spoiler")), default=False),
        emotion=_normalize_optional_text(data.get("emotion")),
    )
    return JSONResponse({"highlight_id": getattr(highlight, "id", None)}, status_code=201)


@highlight_router.get("/feed", name="highlight.get_highlight_feed")
async def get_highlight_feed(request: Request):
    container = get_container(request)
    viewer = get_current_user(request)
    feed = await container.get_highlight_feed_use_case().execute(
        viewer_user_id=viewer.id if viewer else None,
        anime_id=_to_int(request.query_params.get("anime_id")),
        category=request.query_params.get("category") or None,
        include_spoilers=_to_bool(request.query_params.get("include_spoilers"), default=False),
        limit=max(min(_to_int(request.query_params.get("limit")) or 12, 24), 1),
    )
    return render_template(request, "highlight/feed.html", feed=feed)


@highlight_router.get("/following", name="highlight.get_following_highlights")
async def get_following_highlights(request: Request):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return RedirectResponse(
            url=request.app.url_path_for("auth.login_page"),
            status_code=303,
        )
    page = await container.get_following_highlights_use_case().execute(
        follower_user_id=user.id,
        anime_id=_to_int(request.query_params.get("anime_id")),
        emotion=request.query_params.get("emotion") or None,
        category=request.query_params.get("category") or None,
        sort_by=request.query_params.get("sort") or "recent",
        created_date=request.query_params.get("date") or None,
        query=request.query_params.get("query") or None,
        include_spoilers=_to_bool(request.query_params.get("include_spoilers"), default=False),
        limit=max(min(_to_int(request.query_params.get("limit")) or 24, 48), 1),
    )
    return render_template(request, "highlight/following.html", page=page)


@highlight_router.get("/saved", name="highlight.get_saved_highlights")
async def get_saved_highlights(request: Request):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return RedirectResponse(
            url=request.app.url_path_for("auth.login_page"),
            status_code=303,
        )
    dashboard = await container.get_saved_highlights_use_case().execute(
        user_id=user.id,
        anime_id=_to_int(request.query_params.get("anime_id")),
        emotion=request.query_params.get("emotion") or None,
        category=request.query_params.get("category") or None,
        sort_by=request.query_params.get("sort") or "recent",
        created_date=request.query_params.get("date") or None,
        query=request.query_params.get("query") or None,
        include_spoilers=_to_bool(request.query_params.get("include_spoilers"), default=True),
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
async def get_liked_highlights(request: Request):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return RedirectResponse(
            url=request.app.url_path_for("auth.login_page"),
            status_code=303,
        )
    dashboard = await container.get_liked_highlights_use_case().execute(
        user_id=user.id,
        anime_id=_to_int(request.query_params.get("anime_id")),
        emotion=request.query_params.get("emotion") or None,
        category=request.query_params.get("category") or None,
        sort_by=request.query_params.get("sort") or "recent",
        created_date=request.query_params.get("date") or None,
        query=request.query_params.get("query") or None,
        include_spoilers=_to_bool(request.query_params.get("include_spoilers"), default=True),
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
async def get_shared_highlight(request: Request, highlight_id: int):
    container = get_container(request)
    viewer = get_current_user(request)
    try:
        dashboard = await container.get_shared_highlight_use_case().execute(
            highlight_id=highlight_id,
            viewer_user_id=viewer.id if viewer else None,
        )
    except ValueError:
        return render_template(request, "errors/500_modal.html", status_code=404)
    return render_template(
        request,
        "highlight/list.html",
        dashboard=dashboard,
        user_id=None,
        is_public=True,
        view_mode="share",
    )


@highlight_router.get("/notifications", name="highlight.get_highlight_notifications")
async def get_highlight_notifications(request: Request):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return RedirectResponse(
            url=request.app.url_path_for("auth.login_page"),
            status_code=303,
        )
    items = await container.get_highlight_notifications_use_case().execute(
        user_id=user.id,
        limit=max(min(_to_int(request.query_params.get("limit")) or 20, 100), 1),
    )
    return render_template(request, "highlight/notifications.html", items=items)


@highlight_router.get("/top", name="highlight.get_public_top_highlights")
async def get_public_top_highlights(request: Request):
    container = get_container(request)
    viewer = get_current_user(request)
    limit = max(min(_to_int(request.query_params.get("limit")) or 20, 50), 1)
    dashboard = await container.get_public_top_highlights_use_case().execute(
        limit=limit,
        anime_id=_to_int(request.query_params.get("anime_id")),
        emotion=request.query_params.get("emotion") or None,
        category=request.query_params.get("category") or None,
        sort_by=request.query_params.get("sort") or "popular",
        created_date=request.query_params.get("date") or None,
        query=request.query_params.get("query") or None,
        include_spoilers=_to_bool(request.query_params.get("include_spoilers"), default=False),
        viewer_user_id=viewer.id if viewer else None,
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
async def get_user_highlights(request: Request, user_id: int):
    container = get_container(request)
    viewer = get_current_user(request)
    dashboard = await container.get_user_highlights_use_case().execute(
        user_id=user_id,
        anime_id=_to_int(request.query_params.get("anime_id")),
        emotion=request.query_params.get("emotion") or None,
        category=request.query_params.get("category") or None,
        sort_by=request.query_params.get("sort") or "recent",
        created_date=request.query_params.get("date") or None,
        query=request.query_params.get("query") or None,
        include_spoilers=_to_bool(request.query_params.get("include_spoilers"), default=True),
        viewer_user_id=viewer.id if viewer else None,
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
async def edit_highlight(request: Request, highlight_id: int):
    container = get_container(request)
    data = await read_payload(request)
    await container.edit_highlight_use_case().execute(
        highlight_id=highlight_id,
        episode=_to_int(data.get("episode")),
        start_timestamp=_to_seconds(data.get("start_timestamp")),
        end_timestamp=_to_seconds(data.get("end_timestamp")),
        title=str(data.get("title") or "").strip(),
        category=_normalize_optional_text(data.get("category")),
        description=str(data.get("description") or "").strip(),
        is_spoiler=_to_bool(str(data.get("is_spoiler")), default=False),
        emotion=_normalize_optional_text(data.get("emotion")),
    )
    return Response(status_code=204)


@highlight_router.delete("/{highlight_id}", name="highlight.delete_highlight")
async def delete_highlight(request: Request, highlight_id: int):
    container = get_container(request)
    await container.delete_highlight_use_case().execute(highlight_id=highlight_id)
    return Response(status_code=204)


@highlight_router.get("/{highlight_id}/likes", name="highlight.get_highlight_likes")
@highlight_router.post("/{highlight_id}/likes", name="highlight.highlight_likes")
@highlight_router.delete("/{highlight_id}/likes", name="highlight.remove_highlight_like")
@rate_limit(
    scope="highlight_like",
    limit=60,
    window_seconds=60,
    key_builder=lambda request: f"{client_ip(request)}::{getattr(get_current_user(request), 'id', 'guest')}",
)
async def highlight_likes(request: Request, highlight_id: int):
    container = get_container(request)
    if request.method == "GET":
        items = await container.get_highlight_likers_use_case().execute(
            highlight_id=highlight_id,
            limit=max(min(_to_int(request.query_params.get("limit")) or 20, 100), 1),
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

    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    liked = request.method == "POST"
    try:
        highlight = await container.set_highlight_like_use_case().execute(
            highlight_id=highlight_id,
            user_id=user.id,
            liked=liked,
        )
    except ValueError:
        return JSONResponse({"error": "highlight_not_found"}, status_code=404)
    return {
        "highlight_id": highlight.id,
        "liked": liked,
        "likes_count": highlight.likes_count,
    }


@highlight_router.post("/{highlight_id}/save", name="highlight.set_saved_highlight")
@highlight_router.delete("/{highlight_id}/save", name="highlight.unset_saved_highlight")
@rate_limit(
    scope="highlight_save",
    limit=60,
    window_seconds=60,
    key_builder=lambda request: f"{client_ip(request)}::{getattr(get_current_user(request), 'id', 'guest')}",
)
async def set_saved_highlight(request: Request, highlight_id: int):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    saved = request.method == "POST"
    try:
        state = await container.set_saved_highlight_use_case().execute(
            highlight_id=highlight_id,
            user_id=user.id,
            saved=saved,
        )
    except ValueError:
        return JSONResponse({"error": "highlight_not_found"}, status_code=404)
    return {"highlight_id": highlight_id, "saved": state}


@highlight_router.get("/{highlight_id}/comments", name="highlight.get_highlight_comments")
@highlight_router.post("/{highlight_id}/comments", name="highlight.highlight_comments")
@rate_limit(
    scope="highlight_comment",
    limit=30,
    window_seconds=60,
    key_builder=lambda request: f"{client_ip(request)}::{getattr(get_current_user(request), 'id', 'guest')}",
)
async def highlight_comments(request: Request, highlight_id: int):
    container = get_container(request)
    if request.method == "GET":
        items = await container.get_highlight_comments_use_case().execute(
            highlight_id=highlight_id,
            limit=max(min(_to_int(request.query_params.get("limit")) or 20, 100), 1),
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
        return JSONResponse({"error": "auth_required"}, status_code=401)
    data = await read_payload(request)
    try:
        comment = await container.add_highlight_comment_use_case().execute(
            highlight_id=highlight_id,
            user_id=user.id,
            content=str(data.get("content") or "").strip(),
        )
    except ValueError as error:
        status_code = 404 if "не найден" in str(error) else 400
        return JSONResponse({"error": str(error)}, status_code=status_code)
    return JSONResponse(
        {
            "id": comment.id,
            "user_id": comment.user_id,
            "username": comment.username,
            "content": comment.content,
            "created_at": comment.created_at,
        },
        status_code=201,
    )


def _to_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _to_seconds(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    if ":" in text:
        minutes, seconds = text.split(":", 1)
        return float(int(minutes) * 60 + int(seconds))
    return float(text)


def _safe_to_seconds(value) -> float | None:
    try:
        return _to_seconds(value)
    except (TypeError, ValueError):
        return None


def _normalize_optional_text(value) -> str | None:
    text = str(value or "").strip()
    return text or None
