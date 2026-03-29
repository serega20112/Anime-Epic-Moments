import re
from urllib.parse import urljoin, urlparse

import requests
from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    stream_with_context,
    url_for,
)
from sqlalchemy.exc import SQLAlchemyError

from src.backend.dependencies.container import container
from src.backend.domain.anime.value_object import AnimeDiscussionBoard
from src.backend.infrastructure.security.flask_protection import client_ip, rate_limit

watch_bp = Blueprint("watch", __name__, url_prefix="/watch")
_proxy_media_session = requests.Session()
_proxy_media_session.trust_env = False
_allowed_media_host_suffixes = (
    "libria.fun",
    "anilibria.top",
    "anilibria.tv",
    "kodikplayer.com",
    "kodik.info",
    "kodik.biz",
    "kodikapi.com",
)


@watch_bp.route("/<int:anime_id>", methods=["GET"])
def watch_page(anime_id: int):
    episode = _to_int(request.args.get("episode")) or 1
    selected_source_id = _to_int(request.args.get("source_id"))
    preferred_start_seconds = _safe_float(request.args.get("start_at"))
    discussion_sort = str(request.args.get("discussion_sort") or "popular").strip().lower()
    user = getattr(g, "user", None)
    data = container.get_watch_page_use_case().execute(
        anime_id=anime_id,
        episode=episode,
        user_id=user.id if user else None,
        selected_source_id=selected_source_id,
        preferred_start_seconds=preferred_start_seconds,
    )
    discussion = _load_discussion(
        anime_id=anime_id,
        discussion_sort=discussion_sort,
        viewer_user_id=user.id if user else None,
    )
    return render_template("anime/watch.html", watch=data, discussion=discussion)


@watch_bp.route("/proxy", methods=["GET", "HEAD"])
def proxy_stream():
    upstream_url = str(request.args.get("url") or "").strip()
    if not _is_allowed_media_url(upstream_url):
        abort(403)
    request_headers = {"User-Agent": _browser_user_agent()}
    if request.headers.get("Range"):
        request_headers["Range"] = request.headers["Range"]
    try:
        upstream_response = _proxy_media_session.get(
            upstream_url,
            timeout=30,
            stream=True,
            headers=request_headers,
        )
        upstream_response.raise_for_status()
    except requests.RequestException:
        current_app.logger.exception("watch_stream_proxy_failed url=%s", upstream_url)
        return jsonify({"error": "stream_unavailable"}), 502

    content_type = str(upstream_response.headers.get("Content-Type") or "").lower()
    upstream_status = int(getattr(upstream_response, "status_code", 200) or 200)
    if _is_hls_manifest(upstream_url=upstream_url, content_type=content_type):
        manifest_text = upstream_response.text
        upstream_response.close()
        proxied_manifest = _rewrite_hls_manifest(
            manifest_text=manifest_text,
            upstream_url=upstream_url,
        )
        return Response(
            proxied_manifest,
            content_type="application/vnd.apple.mpegurl",
            status=upstream_status,
        )

    response_headers = {}
    if upstream_response.headers.get("Content-Type"):
        response_headers["Content-Type"] = upstream_response.headers["Content-Type"]
    if upstream_response.headers.get("Content-Length"):
        response_headers["Content-Length"] = upstream_response.headers["Content-Length"]
    if upstream_response.headers.get("Accept-Ranges"):
        response_headers["Accept-Ranges"] = upstream_response.headers["Accept-Ranges"]
    if upstream_response.headers.get("Content-Range"):
        response_headers["Content-Range"] = upstream_response.headers["Content-Range"]

    def generate():
        try:
            for chunk in upstream_response.iter_content(chunk_size=64 * 1024):
                if chunk:
                    yield chunk
        finally:
            upstream_response.close()

    return Response(
        stream_with_context(generate()),
        headers=response_headers,
        status=upstream_status,
    )


@watch_bp.route("/<int:anime_id>/status", methods=["POST"])
def update_status(anime_id: int):
    user = getattr(g, "user", None)
    if not user:
        return jsonify({"error": "auth_required"}), 401
    payload = request.get_json(silent=True) or {}
    status = str(payload.get("status") or "").strip()
    if not status:
        return jsonify({"error": "status_required"}), 400
    result = container.upsert_user_anime_status_use_case().execute(
        user_id=user.id,
        anime_id=anime_id,
        status=status,
    )
    return jsonify({"status": result.status})


@watch_bp.route("/<int:anime_id>/sources", methods=["POST"])
def add_source(anime_id: int):
    return jsonify({"error": "manual_source_creation_disabled"}), 403


@watch_bp.route("/<int:anime_id>/sources/discover", methods=["POST"])
@rate_limit(
    container_getter=lambda: container,
    scope="watch_discover_sources",
    limit=15,
    window_seconds=60,
    key_builder=lambda: f"{client_ip()}::{request.view_args.get('anime_id')}",
)
def discover_sources(anime_id: int):
    payload = request.get_json(silent=True) or request.form
    episode = _to_int(str(payload.get("episode") or "")) or 1
    result = container.sync_watch_sources_use_case().execute(
        anime_id=anime_id,
        episode=episode,
        force=True,
    )
    if not result["enabled"]:
        return jsonify({"error": "provider_not_configured"}), 400
    return jsonify(result)


@watch_bp.route("/<int:anime_id>/session", methods=["POST"])
def save_session(anime_id: int):
    user = getattr(g, "user", None)
    if not user:
        return jsonify({"error": "auth_required"}), 401
    payload = request.get_json(silent=True) or {}
    episode = _to_int(str(payload.get("episode") or ""))
    watch_source_id = _to_int(str(payload.get("watch_source_id") or ""))
    if episode is None or watch_source_id is None:
        return jsonify({"error": "invalid_payload"}), 400
    session = container.save_viewing_session_use_case().execute(
        user_id=user.id,
        anime_id=anime_id,
        episode=episode,
        watch_source_id=watch_source_id,
        position_seconds=float(payload.get("position_seconds") or 0.0),
        volume=float(payload.get("volume") or 1.0),
        quality_label=str(payload.get("quality_label") or "Auto"),
        is_paused=bool(payload.get("is_paused")),
    )
    return jsonify({"session_id": session.id})


@watch_bp.route("/<int:anime_id>/highlights", methods=["POST"])
@rate_limit(
    container_getter=lambda: container,
    scope="watch_create_highlight",
    limit=20,
    window_seconds=60,
    key_builder=lambda: f"{client_ip()}::{getattr(g, 'user', None).id if getattr(g, 'user', None) else 'guest'}",
)
def create_highlight(anime_id: int):
    user = getattr(g, "user", None)
    if not user:
        return jsonify({"error": "auth_required"}), 401
    payload = request.get_json(silent=True) or {}
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
        return jsonify({"error": "invalid_payload"}), 400
    highlight = container.create_watch_highlight_use_case().execute(
        user_id=user.id,
        anime_id=anime_id,
        episode=episode,
        title=str(payload.get("title") or "").strip(),
        category=(
            str(payload.get("category")).strip()
            if payload.get("category") is not None
            else None
        ),
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        description=str(payload.get("description") or "").strip(),
        is_spoiler=_to_bool(payload.get("is_spoiler")),
        emotion=(
            str(payload.get("emotion")).strip()
            if payload.get("emotion") is not None
            else None
        ),
        watch_source_id=watch_source_id,
        translation_id=translation_id,
    )
    return jsonify({"highlight_id": highlight.id}), 201


@watch_bp.route("/<int:anime_id>/discussion", methods=["POST"])
def add_anime_comment(anime_id: int):
    user = getattr(g, "user", None)
    if not user:
        return jsonify({"error": "auth_required"}), 401
    payload = request.get_json(silent=True) or request.form
    content = str(payload.get("content") or "").strip()
    try:
        comment = container.add_anime_comment_use_case().execute(
            anime_id=anime_id,
            user_id=user.id,
            content=content,
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except SQLAlchemyError:
        current_app.logger.exception("anime_discussion_comment_unavailable")
        return _discussion_unavailable_response(anime_id=anime_id, payload=payload)
    if request.is_json:
        return jsonify(vars(comment)), 201
    return redirect(
        url_for(
            "watch.watch_page",
            anime_id=anime_id,
            episode=_to_int(str(payload.get("episode") or "")) or 1,
            discussion_sort=str(payload.get("discussion_sort") or "popular"),
        )
    )


@watch_bp.route("/discussion/comments/<int:comment_id>/likes", methods=["POST", "DELETE"])
def set_anime_comment_like(comment_id: int):
    user = getattr(g, "user", None)
    if not user:
        return jsonify({"error": "auth_required"}), 401
    liked = request.method == "POST"
    try:
        comment = container.set_anime_comment_like_use_case().execute(
            comment_id=comment_id,
            user_id=user.id,
            liked=liked,
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 404
    except SQLAlchemyError:
        current_app.logger.exception("anime_discussion_like_unavailable")
        return jsonify({"error": "discussion_unavailable"}), 503
    return jsonify(vars(comment))


@watch_bp.route("/open/<int:anime_id>", methods=["GET"])
def redirect_to_watch(anime_id: int):
    episode = _to_int(request.args.get("episode")) or 1
    return redirect(url_for("watch.watch_page", anime_id=anime_id, episode=episode))


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


def _load_discussion(
    anime_id: int,
    discussion_sort: str,
    viewer_user_id: int | None,
) -> AnimeDiscussionBoard:
    normalized_sort = (
        discussion_sort if discussion_sort in {"popular", "recent"} else "popular"
    )
    try:
        return container.get_anime_discussion_use_case().execute(
            anime_id=anime_id,
            sort_by=normalized_sort,
            viewer_user_id=viewer_user_id,
            limit=20,
        )
    except SQLAlchemyError:
        current_app.logger.exception("anime_discussion_unavailable")
        return AnimeDiscussionBoard(
            anime_id=anime_id,
            items=[],
            selected_sort=normalized_sort,
            total_comments=0,
        )


def _discussion_unavailable_response(anime_id: int, payload):
    if request.is_json:
        return jsonify({"error": "discussion_unavailable"}), 503
    return redirect(
        url_for(
            "watch.watch_page",
            anime_id=anime_id,
            episode=_to_int(str(payload.get("episode") or "")) or 1,
            discussion_sort=str(payload.get("discussion_sort") or "popular"),
        )
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


def _rewrite_hls_manifest(manifest_text: str, upstream_url: str) -> str:
    rewritten_lines: list[str] = []
    for line in manifest_text.splitlines():
        stripped = line.strip()
        if not stripped:
            rewritten_lines.append(line)
            continue
        if stripped.startswith("#"):
            rewritten_lines.append(_rewrite_manifest_uri_attributes(line, upstream_url))
            continue
        absolute_url = urljoin(upstream_url, stripped)
        rewritten_lines.append(_build_proxy_url(absolute_url))
    return "\n".join(rewritten_lines)


def _rewrite_manifest_uri_attributes(line: str, upstream_url: str) -> str:
    def replace(match):
        absolute_url = urljoin(upstream_url, match.group("uri"))
        return f'URI="{_build_proxy_url(absolute_url)}"'

    return re.sub(r'URI="(?P<uri>[^"]+)"', replace, line)


def _build_proxy_url(upstream_url: str) -> str:
    return url_for("watch.proxy_stream", url=upstream_url)


def _browser_user_agent() -> str:
    user_agent = str(request.headers.get("User-Agent") or "").strip()
    return user_agent or "Mozilla/5.0"
