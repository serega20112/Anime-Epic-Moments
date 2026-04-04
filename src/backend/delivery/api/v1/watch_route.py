import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response, StreamingResponse

from src.backend.delivery.api.helpers import (
    get_container,
    get_current_user,
    read_payload,
)
from src.backend.domain.anime.value_object import AnimeDiscussionBoard
from src.backend.infrastructure.security.flask_protection import client_ip, rate_limit
from src.backend.infrastructure.web.templating import render_template

watch_router = APIRouter(prefix="/watch")
watch_bp = watch_router
container = None
logger = logging.getLogger("anime_epic_moments")
_proxy_media_client = httpx.AsyncClient(follow_redirects=True, trust_env=False, timeout=30.0)
_allowed_media_host_suffixes = (
    "libria.fun",
    "anilibria.top",
    "anilibria.tv",
    "kodikplayer.com",
    "kodik.info",
    "kodik.biz",
    "kodikapi.com",
)


@watch_router.get("/proxy", name="watch.proxy_stream")
@watch_router.head("/proxy", name="watch.proxy_stream_head")
async def proxy_stream(request: Request):
    upstream_url = str(request.query_params.get("url") or "").strip()
    if not _is_allowed_media_url(upstream_url):
        return Response(status_code=403)
    request_headers = {"User-Agent": _browser_user_agent(request)}
    if request.headers.get("Range"):
        request_headers["Range"] = request.headers["Range"]
    try:
        upstream_response = await _proxy_media_client.get(
            upstream_url,
            headers=request_headers,
        )
        upstream_response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("watch_stream_proxy_failed url=%s", upstream_url)
        return JSONResponse({"error": "stream_unavailable"}, status_code=502)

    content_type = str(upstream_response.headers.get("Content-Type") or "").lower()
    upstream_status = int(upstream_response.status_code or 200)
    if _is_hls_manifest(upstream_url=upstream_url, content_type=content_type):
        proxied_manifest = _rewrite_hls_manifest(
            request=request,
            manifest_text=upstream_response.text,
            upstream_url=upstream_url,
        )
        return Response(
            content=proxied_manifest,
            media_type="application/vnd.apple.mpegurl",
            status_code=upstream_status,
        )

    async def generate():
        async with _proxy_media_client.stream(
            "GET",
            upstream_url,
            headers=request_headers,
        ) as stream_response:
            async for chunk in stream_response.aiter_bytes(chunk_size=64 * 1024):
                if chunk:
                    yield chunk

    response_headers = {}
    for header_name in (
        "Content-Type",
        "Content-Length",
        "Accept-Ranges",
        "Content-Range",
    ):
        if upstream_response.headers.get(header_name):
            response_headers[header_name] = upstream_response.headers[header_name]
    return StreamingResponse(
        generate(),
        headers=response_headers,
        status_code=upstream_status,
    )


@watch_router.get("/{anime_id}", name="watch.watch_page")
async def watch_page(request: Request, anime_id: int):
    container = get_container(request)
    user = get_current_user(request)
    episode = _to_int(request.query_params.get("episode")) or 1
    selected_source_id = _to_int(request.query_params.get("source_id"))
    preferred_start_seconds = _safe_float(request.query_params.get("start_at"))
    discussion_sort = str(request.query_params.get("discussion_sort") or "popular").strip().lower()
    data = await container.get_watch_page_use_case().execute(
        anime_id=anime_id,
        episode=episode,
        user_id=user.id if user else None,
        selected_source_id=selected_source_id,
        preferred_start_seconds=preferred_start_seconds,
    )
    discussion = await _load_discussion(
        request=request,
        anime_id=anime_id,
        discussion_sort=discussion_sort,
        viewer_user_id=user.id if user else None,
    )
    return render_template(request, "anime/watch.html", watch=data, discussion=discussion)


@watch_router.post("/{anime_id}/status", name="watch.update_status")
async def update_status(request: Request, anime_id: int):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    payload = await read_payload(request)
    status = str(payload.get("status") or "").strip()
    if not status:
        return JSONResponse({"error": "status_required"}, status_code=400)
    result = await container.upsert_user_anime_status_use_case().execute(
        user_id=user.id,
        anime_id=anime_id,
        status=status,
    )
    return {"status": result.status}


@watch_router.post("/{anime_id}/sources", name="watch.add_source")
async def add_source(_request: Request, anime_id: int):
    return JSONResponse({"error": "manual_source_creation_disabled"}, status_code=403)


@watch_router.post("/{anime_id}/sources/discover", name="watch.discover_sources")
@rate_limit(
    scope="watch_discover_sources",
    limit=15,
    window_seconds=60,
    key_builder=lambda request: f"{client_ip(request)}::{request.path_params.get('anime_id')}",
)
async def discover_sources(request: Request, anime_id: int):
    container = get_container(request)
    payload = await read_payload(request)
    episode = _to_int(str(payload.get("episode") or "")) or 1
    result = await container.sync_watch_sources_use_case().execute(
        anime_id=anime_id,
        episode=episode,
        force=True,
    )
    if not result["enabled"]:
        return JSONResponse({"error": "provider_not_configured"}, status_code=400)
    return result


@watch_router.post("/{anime_id}/session", name="watch.save_session")
async def save_session(request: Request, anime_id: int):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    payload = await read_payload(request)
    episode = _to_int(str(payload.get("episode") or ""))
    watch_source_id = _to_int(str(payload.get("watch_source_id") or ""))
    if episode is None or watch_source_id is None:
        return JSONResponse({"error": "invalid_payload"}, status_code=400)
    session = await container.save_viewing_session_use_case().execute(
        user_id=user.id,
        anime_id=anime_id,
        episode=episode,
        watch_source_id=watch_source_id,
        position_seconds=float(payload.get("position_seconds") or 0.0),
        volume=float(payload.get("volume") or 1.0),
        quality_label=str(payload.get("quality_label") or "Auto"),
        is_paused=bool(payload.get("is_paused")),
    )
    return {"session_id": session.id}


@watch_router.post("/{anime_id}/highlights", name="watch.create_highlight")
@rate_limit(
    scope="watch_create_highlight",
    limit=20,
    window_seconds=60,
    key_builder=lambda request: f"{client_ip(request)}::{getattr(get_current_user(request), 'id', 'guest')}",
)
async def create_highlight(request: Request, anime_id: int):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    payload = await read_payload(request)
    episode = _to_int(str(payload.get("episode") or ""))
    watch_source_id = _to_int(str(payload.get("watch_source_id") or ""))
    translation_id = _to_int(str(payload.get("translation_id") or ""))
    start_timestamp = _safe_float(payload.get("start_timestamp"))
    end_timestamp = _safe_float(payload.get("end_timestamp"))
    if (
        episode is None
        or watch_source_id is None
        or translation_id is None
        or start_timestamp is None
        or end_timestamp is None
    ):
        return JSONResponse({"error": "invalid_payload"}, status_code=400)
    highlight = await container.create_watch_highlight_use_case().execute(
        user_id=user.id,
        anime_id=anime_id,
        episode=episode,
        title=str(payload.get("title") or "").strip(),
        category=(str(payload.get("category")).strip() if payload.get("category") is not None else None),
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        description=str(payload.get("description") or "").strip(),
        is_spoiler=_to_bool(payload.get("is_spoiler")),
        emotion=(str(payload.get("emotion")).strip() if payload.get("emotion") is not None else None),
        watch_source_id=watch_source_id,
        translation_id=translation_id,
    )
    return JSONResponse({"highlight_id": highlight.id}, status_code=201)


@watch_router.post("/{anime_id}/discussion", name="watch.add_anime_comment")
async def add_anime_comment(request: Request, anime_id: int):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    payload = await read_payload(request)
    content = str(payload.get("content") or "").strip()
    try:
        comment = await container.add_anime_comment_use_case().execute(
            anime_id=anime_id,
            user_id=user.id,
            content=content,
        )
    except ValueError as error:
        return JSONResponse({"error": str(error)}, status_code=400)
    except Exception:
        logger.exception("anime_discussion_comment_unavailable")
        return _discussion_unavailable_response(
            request=request,
            anime_id=anime_id,
            payload=payload,
        )
    if "application/json" in str(request.headers.get("content-type") or "").lower():
        return JSONResponse(vars(comment), status_code=201)
    return RedirectResponse(
        url=(
            f"{request.app.url_path_for('watch.watch_page', anime_id=str(anime_id))}"
            f"?episode={_to_int(str(payload.get('episode') or '')) or 1}"
            f"&discussion_sort={str(payload.get('discussion_sort') or 'popular')}"
        ),
        status_code=303,
    )


@watch_router.post("/discussion/comments/{comment_id}/likes", name="watch.set_anime_comment_like")
@watch_router.delete("/discussion/comments/{comment_id}/likes", name="watch.remove_anime_comment_like")
async def set_anime_comment_like(request: Request, comment_id: int):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    liked = request.method == "POST"
    try:
        comment = await container.set_anime_comment_like_use_case().execute(
            comment_id=comment_id,
            user_id=user.id,
            liked=liked,
        )
    except ValueError as error:
        return JSONResponse({"error": str(error)}, status_code=404)
    except Exception:
        logger.exception("anime_discussion_like_unavailable")
        return JSONResponse({"error": "discussion_unavailable"}, status_code=503)
    return vars(comment)


@watch_router.get("/open/{anime_id}", name="watch.redirect_to_watch")
async def redirect_to_watch(request: Request, anime_id: int):
    episode = _to_int(request.query_params.get("episode")) or 1
    return RedirectResponse(
        url=f"{request.app.url_path_for('watch.watch_page', anime_id=str(anime_id))}?episode={episode}",
        status_code=303,
    )


def _to_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _safe_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


async def _load_discussion(
    request: Request,
    anime_id: int,
    discussion_sort: str,
    viewer_user_id: int | None,
) -> AnimeDiscussionBoard:
    normalized_sort = discussion_sort if discussion_sort in {"popular", "recent"} else "popular"
    try:
        return await get_container(request).get_anime_discussion_use_case().execute(
            anime_id=anime_id,
            sort_by=normalized_sort,
            viewer_user_id=viewer_user_id,
            limit=20,
        )
    except Exception:
        logger.exception("anime_discussion_unavailable")
        return AnimeDiscussionBoard(
            anime_id=anime_id,
            items=[],
            selected_sort=normalized_sort,
            total_comments=0,
        )


def _discussion_unavailable_response(request: Request, anime_id: int, payload):
    if "application/json" in str(request.headers.get("content-type") or "").lower():
        return JSONResponse({"error": "discussion_unavailable"}, status_code=503)
    return RedirectResponse(
        url=(
            f"{request.app.url_path_for('watch.watch_page', anime_id=str(anime_id))}"
            f"?episode={_to_int(str(payload.get('episode') or '')) or 1}"
            f"&discussion_sort={str(payload.get('discussion_sort') or 'popular')}"
        ),
        status_code=303,
    )


def _is_allowed_media_url(value: str) -> bool:
    parsed = urlparse(str(value or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    hostname = (parsed.hostname or "").lower()
    return any(
        hostname == suffix or hostname.endswith(f".{suffix}")
        for suffix in _allowed_media_host_suffixes
    )


def _is_hls_manifest(upstream_url: str, content_type: str) -> bool:
    return ".m3u8" in upstream_url.lower() or "mpegurl" in content_type


def _rewrite_hls_manifest(request: Request, manifest_text: str, upstream_url: str) -> str:
    rewritten_lines: list[str] = []
    for line in manifest_text.splitlines():
        stripped = line.strip()
        if not stripped:
            rewritten_lines.append(line)
            continue
        if stripped.startswith("#"):
            rewritten_lines.append(_rewrite_manifest_uri_attributes(request, line, upstream_url))
            continue
        absolute_url = urljoin(upstream_url, stripped)
        rewritten_lines.append(_build_proxy_url(request, absolute_url))
    return "\n".join(rewritten_lines)


def _rewrite_manifest_uri_attributes(request: Request, line: str, upstream_url: str) -> str:
    def replace(match):
        absolute_url = urljoin(upstream_url, match.group("uri"))
        return f'URI="{_build_proxy_url(request, absolute_url)}"'

    return re.sub(r'URI="(?P<uri>[^"]+)"', replace, line)


def _build_proxy_url(request: Request, upstream_url: str) -> str:
    return f"{request.app.url_path_for('watch.proxy_stream')}?url={upstream_url}"


def _browser_user_agent(request: Request) -> str:
    user_agent = str(request.headers.get("User-Agent") or "").strip()
    return user_agent or "Mozilla/5.0"


async def close_watch_route_clients():
    await _proxy_media_client.aclose()
