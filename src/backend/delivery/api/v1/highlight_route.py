from flask import Blueprint, g, jsonify, redirect, render_template, request, url_for

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
    highlight = container.create_highlight_use_case().execute(
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
    return jsonify({"highlight_id": getattr(highlight, "id", None)}), 201


@highlight_bp.route("/feed", methods=["GET"])
def get_highlight_feed():
    """Рендерит социальный фид хайлайтов с персональными секциями."""
    viewer = getattr(g, "user", None)
    feed = container.get_highlight_feed_use_case().execute(
        viewer_user_id=viewer.id if viewer else None,
        anime_id=_to_int(request.args.get("anime_id")),
        category=request.args.get("category") or None,
        include_spoilers=_to_bool(request.args.get("include_spoilers"), default=False),
        limit=max(min(_to_int(request.args.get("limit")) or 12, 24), 1),
    )
    return render_template("highlight/feed.html", feed=feed)


@highlight_bp.route("/following", methods=["GET"])
def get_following_highlights():
    """Рендерит ленту хайлайтов пользователей, на которых подписан текущий зритель."""
    user = getattr(g, "user", None)
    if not user:
        return redirect(url_for("auth.login_page"))
    page = container.get_following_highlights_use_case().execute(
        follower_user_id=user.id,
        anime_id=_to_int(request.args.get("anime_id")),
        emotion=request.args.get("emotion") or None,
        category=request.args.get("category") or None,
        sort_by=request.args.get("sort") or "recent",
        created_date=request.args.get("date") or None,
        query=request.args.get("query") or None,
        include_spoilers=_to_bool(request.args.get("include_spoilers"), default=False),
        limit=max(min(_to_int(request.args.get("limit")) or 24, 48), 1),
    )
    return render_template("highlight/following.html", page=page)


@highlight_bp.route("/saved", methods=["GET"])
def get_saved_highlights():
    """Рендер страницы с сохраненными хайлайтами текущего пользователя."""
    user = getattr(g, "user", None)
    if not user:
        return redirect(url_for("auth.login_page"))
    dashboard = container.get_saved_highlights_use_case().execute(
        user_id=user.id,
        anime_id=_to_int(request.args.get("anime_id")),
        emotion=request.args.get("emotion") or None,
        category=request.args.get("category") or None,
        sort_by=request.args.get("sort") or "recent",
        created_date=request.args.get("date") or None,
        query=request.args.get("query") or None,
        include_spoilers=_to_bool(request.args.get("include_spoilers"), default=True),
    )
    return render_template(
        "highlight/list.html",
        dashboard=dashboard,
        user_id=user.id,
        is_public=False,
        view_mode="saved",
    )


@highlight_bp.route("/liked", methods=["GET"])
def get_liked_highlights():
    """Рендер страницы с лайкнутыми хайлайтами текущего пользователя."""
    user = getattr(g, "user", None)
    if not user:
        return redirect(url_for("auth.login_page"))
    dashboard = container.get_liked_highlights_use_case().execute(
        user_id=user.id,
        anime_id=_to_int(request.args.get("anime_id")),
        emotion=request.args.get("emotion") or None,
        category=request.args.get("category") or None,
        sort_by=request.args.get("sort") or "recent",
        created_date=request.args.get("date") or None,
        query=request.args.get("query") or None,
        include_spoilers=_to_bool(request.args.get("include_spoilers"), default=True),
    )
    return render_template(
        "highlight/list.html",
        dashboard=dashboard,
        user_id=user.id,
        is_public=False,
        view_mode="liked",
    )


@highlight_bp.route("/share/<int:highlight_id>", methods=["GET"])
def get_shared_highlight(highlight_id: int):
    """Рендер страницы одного хайлайта для шеринга."""
    viewer = getattr(g, "user", None)
    try:
        dashboard = container.get_shared_highlight_use_case().execute(
            highlight_id=highlight_id,
            viewer_user_id=viewer.id if viewer else None,
        )
    except ValueError:
        return render_template("errors/500_modal.html"), 404
    return render_template(
        "highlight/list.html",
        dashboard=dashboard,
        user_id=None,
        is_public=True,
        view_mode="share",
    )


@highlight_bp.route("/notifications", methods=["GET"])
def get_highlight_notifications():
    """Рендер страницы с уведомлениями по реакциям на хайлайты пользователя."""
    user = getattr(g, "user", None)
    if not user:
        return redirect(url_for("auth.login_page"))
    items = container.get_highlight_notifications_use_case().execute(
        user_id=user.id,
        limit=max(min(_to_int(request.args.get("limit")) or 20, 100), 1),
    )
    return render_template("highlight/notifications.html", items=items)


@highlight_bp.route("/<int:user_id>", methods=["GET"])
def get_user_highlights(user_id: int):
    """Рендер страницы со списком хайлайтов пользователя"""
    viewer = getattr(g, "user", None)
    dashboard = container.get_user_highlights_use_case().execute(
        user_id=user_id,
        anime_id=_to_int(request.args.get("anime_id")),
        emotion=request.args.get("emotion") or None,
        category=request.args.get("category") or None,
        sort_by=request.args.get("sort") or "recent",
        created_date=request.args.get("date") or None,
        query=request.args.get("query") or None,
        include_spoilers=_to_bool(request.args.get("include_spoilers"), default=True),
        viewer_user_id=viewer.id if viewer else None,
    )
    return render_template(
        "highlight/list.html",
        dashboard=dashboard,
        user_id=user_id,
        is_public=False,
        view_mode="user",
    )


@highlight_bp.route("/top", methods=["GET"])
def get_public_top_highlights():
    """Рендер страницы с топовыми публичными хайлайтами"""
    limit = max(min(_to_int(request.args.get("limit")) or 20, 50), 1)
    viewer = getattr(g, "user", None)
    dashboard = container.get_public_top_highlights_use_case().execute(
        limit=limit,
        anime_id=_to_int(request.args.get("anime_id")),
        emotion=request.args.get("emotion") or None,
        category=request.args.get("category") or None,
        sort_by=request.args.get("sort") or "popular",
        created_date=request.args.get("date") or None,
        query=request.args.get("query") or None,
        include_spoilers=_to_bool(request.args.get("include_spoilers"), default=False),
        viewer_user_id=viewer.id if viewer else None,
    )
    return render_template(
        "highlight/list.html",
        dashboard=dashboard,
        user_id=None,
        is_public=True,
        view_mode="public",
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
        title=str(data.get("title") or "").strip(),
        category=_normalize_optional_text(data.get("category")),
        description=str(data.get("description") or "").strip(),
        is_spoiler=_to_bool(str(data.get("is_spoiler")), default=False),
        emotion=_normalize_optional_text(data.get("emotion")),
    )
    return "", 204


@highlight_bp.route("/<int:highlight_id>", methods=["DELETE"])
def delete_highlight(highlight_id: int):
    """Удаление хайлайта"""
    container.delete_highlight_use_case().execute(highlight_id=highlight_id)
    return "", 204


@highlight_bp.route("/<int:highlight_id>/likes", methods=["GET", "POST", "DELETE"])
@rate_limit(
    container_getter=lambda: container,
    scope="highlight_like",
    limit=60,
    window_seconds=60,
    key_builder=lambda: f"{client_ip()}::{getattr(g, 'user', None).id if getattr(g, 'user', None) else 'guest'}",
)
def highlight_likes(highlight_id: int):
    """Возвращает список лайкнувших или переключает лайк текущего пользователя."""
    if request.method == "GET":
        items = container.get_highlight_likers_use_case().execute(
            highlight_id=highlight_id,
            limit=max(min(_to_int(request.args.get("limit")) or 20, 100), 1),
        )
        return jsonify(
            {
                "items": [
                    {
                        "user_id": item.user_id,
                        "username": item.username,
                        "created_at": item.created_at,
                    }
                    for item in items
                ]
            }
        )

    user = getattr(g, "user", None)
    if not user:
        return jsonify({"error": "auth_required"}), 401
    liked = request.method == "POST"
    try:
        highlight = container.set_highlight_like_use_case().execute(
            highlight_id=highlight_id,
            user_id=user.id,
            liked=liked,
        )
    except ValueError:
        return jsonify({"error": "highlight_not_found"}), 404
    return jsonify(
        {
            "highlight_id": highlight.id,
            "liked": liked,
            "likes_count": highlight.likes_count,
        }
    )


@highlight_bp.route("/<int:highlight_id>/save", methods=["POST", "DELETE"])
@rate_limit(
    container_getter=lambda: container,
    scope="highlight_save",
    limit=60,
    window_seconds=60,
    key_builder=lambda: f"{client_ip()}::{getattr(g, 'user', None).id if getattr(g, 'user', None) else 'guest'}",
)
def set_saved_highlight(highlight_id: int):
    """Сохраняет или удаляет хайлайт из сохраненных."""
    user = getattr(g, "user", None)
    if not user:
        return jsonify({"error": "auth_required"}), 401
    saved = request.method == "POST"
    try:
        state = container.set_saved_highlight_use_case().execute(
            highlight_id=highlight_id,
            user_id=user.id,
            saved=saved,
        )
    except ValueError:
        return jsonify({"error": "highlight_not_found"}), 404
    return jsonify({"highlight_id": highlight_id, "saved": state})


@highlight_bp.route("/<int:highlight_id>/comments", methods=["GET", "POST"])
@rate_limit(
    container_getter=lambda: container,
    scope="highlight_comment",
    limit=30,
    window_seconds=60,
    key_builder=lambda: f"{client_ip()}::{getattr(g, 'user', None).id if getattr(g, 'user', None) else 'guest'}",
)
def highlight_comments(highlight_id: int):
    """Возвращает или добавляет комментарии к хайлайту."""
    if request.method == "GET":
        items = container.get_highlight_comments_use_case().execute(
            highlight_id=highlight_id,
            limit=max(min(_to_int(request.args.get("limit")) or 20, 100), 1),
        )
        return jsonify(
            {
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
        )

    user = getattr(g, "user", None)
    if not user:
        return jsonify({"error": "auth_required"}), 401
    data = request.get_json(silent=True) or request.form
    try:
        comment = container.add_highlight_comment_use_case().execute(
            highlight_id=highlight_id,
            user_id=user.id,
            content=str(data.get("content") or "").strip(),
        )
    except ValueError as error:
        status_code = 404 if "не найден" in str(error) else 400
        return jsonify({"error": str(error)}), status_code
    return (
        jsonify(
            {
                "id": comment.id,
                "user_id": comment.user_id,
                "username": comment.username,
                "content": comment.content,
                "created_at": comment.created_at,
            }
        ),
        201,
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


def _normalize_optional_text(value) -> str | None:
    text = str(value or "").strip()
    return text or None
