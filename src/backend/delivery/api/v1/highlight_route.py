from flask import Blueprint, request, render_template, jsonify
from src.backend.dependencies.container import container
from src.backend.infrastructure.security.flask_protection import client_ip, rate_limit

highlight_bp = Blueprint("highlight", __name__, url_prefix="/highlights")


@highlight_bp.route("/", methods=["POST"])
@rate_limit(
    container_getter=lambda: container,
    scope="highlight_create",
    limit=20,
    window_seconds=60,
    key_builder=lambda: f"{client_ip()}::{request.values.get('user_id') or 'guest'}",
)
def create_highlight():
    """Создание нового хайлайта"""
    data = request.get_json(silent=True) or request.form
    anime_id = _to_int(data.get("anime_id"))
    episode = _to_int(data.get("episode"))
    start_timestamp = _safe_to_seconds(data.get("start_timestamp"))
    end_timestamp = _safe_to_seconds(data.get("end_timestamp"))
    if anime_id is None or episode is None or start_timestamp is None or end_timestamp is None:
        return jsonify({"error": "invalid_payload"}), 400
    container.create_highlight_use_case().execute(
        user_id=_to_int(data.get("user_id")),
        anime_id=anime_id,
        episode=episode,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        description=data.get("description", ""),
        is_spoiler=_to_bool(str(data.get("is_spoiler")), default=False),
        emotion=data.get("emotion"),
    )
    return "", 201


@highlight_bp.route("/<int:user_id>", methods=["GET"])
def get_user_highlights(user_id: int):
    """Рендер страницы со списком хайлайтов пользователя"""
    dashboard = container.get_user_highlights_use_case().execute(
        user_id=user_id,
        anime_id=_to_int(request.args.get("anime_id")),
        emotion=request.args.get("emotion") or None,
        created_date=request.args.get("date") or None,
        query=request.args.get("query") or None,
        include_spoilers=_to_bool(request.args.get("include_spoilers"), default=True),
    )
    return render_template(
        "highlight/list.html", dashboard=dashboard, user_id=user_id, is_public=False
    )


@highlight_bp.route("/top", methods=["GET"])
def get_public_top_highlights():
    """Рендер страницы с топовыми публичными хайлайтами"""
    limit = max(min(_to_int(request.args.get("limit")) or 20, 50), 1)
    dashboard = container.get_public_top_highlights_use_case().execute(
        limit=limit,
        anime_id=_to_int(request.args.get("anime_id")),
        emotion=request.args.get("emotion") or None,
        created_date=request.args.get("date") or None,
        query=request.args.get("query") or None,
        include_spoilers=_to_bool(request.args.get("include_spoilers"), default=False),
    )
    return render_template(
        "highlight/list.html", dashboard=dashboard, user_id=None, is_public=True
    )


@highlight_bp.route("/<int:highlight_id>", methods=["PUT"])
def edit_highlight(highlight_id: int):
    """Редактирование существующего хайлайта"""
    data = request.get_json(silent=True) or request.form
    container.edit_highlight_use_case().execute(
        highlight_id=highlight_id,
        episode=_to_int(data.get("episode")),
        start_timestamp=_to_seconds(data.get("start_timestamp")),
        end_timestamp=_to_seconds(data.get("end_timestamp")),
        description=data.get("description") or "",
        is_spoiler=_to_bool(str(data.get("is_spoiler")), default=False),
        emotion=data.get("emotion"),
    )
    return "", 204


@highlight_bp.route("/<int:highlight_id>", methods=["DELETE"])
def delete_highlight(highlight_id: int):
    """Удаление хайлайта"""
    container.delete_highlight_use_case().execute(highlight_id=highlight_id)
    return "", 204


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
    return value.strip().lower() in {"1", "true", "yes", "on"}


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
