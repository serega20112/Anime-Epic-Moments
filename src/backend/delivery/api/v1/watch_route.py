from flask import Blueprint, g, jsonify, redirect, render_template, request, url_for
from src.backend.dependencies.container import container

watch_bp = Blueprint("watch", __name__, url_prefix="/watch")


@watch_bp.route("/<int:anime_id>", methods=["GET"])
def watch_page(anime_id: int):
    episode = _to_int(request.args.get("episode")) or 1
    selected_source_id = _to_int(request.args.get("source_id"))
    user = getattr(g, "user", None)
    data = container.get_watch_page_use_case().execute(
        anime_id=anime_id,
        episode=episode,
        user_id=user.id if user else None,
        selected_source_id=selected_source_id,
    )
    return render_template("anime/watch.html", watch=data)


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
    user = getattr(g, "user", None)
    if not user:
        return jsonify({"error": "auth_required"}), 401
    payload = request.get_json(silent=True) or request.form
    source = container.add_watch_source_use_case().execute(
        anime_id=anime_id,
        episode=int(payload.get("episode")),
        translation_name=str(payload.get("translation_name") or "").strip(),
        translation_type=str(payload.get("translation_type") or "voice").strip(),
        provider_name=str(payload.get("provider_name") or "").strip(),
        source_name=str(payload.get("source_name") or "").strip(),
        stream_url=str(payload.get("stream_url") or "").strip(),
        quality_label=str(payload.get("quality_label") or "Auto").strip(),
        language=str(payload.get("language") or "ru").strip(),
    )
    return jsonify({"source_id": source.id}), 201


@watch_bp.route("/<int:anime_id>/sources/discover", methods=["POST"])
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
    session = container.save_viewing_session_use_case().execute(
        user_id=user.id,
        anime_id=anime_id,
        episode=int(payload.get("episode")),
        watch_source_id=int(payload.get("watch_source_id")),
        position_seconds=float(payload.get("position_seconds") or 0.0),
        volume=float(payload.get("volume") or 1.0),
        quality_label=str(payload.get("quality_label") or "Auto"),
        is_paused=bool(payload.get("is_paused")),
    )
    return jsonify({"session_id": session.id})


@watch_bp.route("/<int:anime_id>/highlights", methods=["POST"])
def create_highlight(anime_id: int):
    user = getattr(g, "user", None)
    if not user:
        return jsonify({"error": "auth_required"}), 401
    payload = request.get_json(silent=True) or {}
    highlight = container.create_watch_highlight_use_case().execute(
        user_id=user.id,
        anime_id=anime_id,
        episode=int(payload.get("episode")),
        title=str(payload.get("title") or "").strip(),
        start_timestamp=float(payload.get("start_timestamp")),
        end_timestamp=float(payload.get("end_timestamp")),
        description=str(payload.get("description") or "").strip(),
        is_spoiler=bool(payload.get("is_spoiler")),
        emotion=(str(payload.get("emotion")).strip() if payload.get("emotion") is not None else None),
        watch_source_id=int(payload.get("watch_source_id")),
        translation_id=int(payload.get("translation_id")),
    )
    return jsonify({"highlight_id": highlight.id}), 201


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
