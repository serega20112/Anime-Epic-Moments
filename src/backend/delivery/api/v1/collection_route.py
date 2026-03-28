from flask import Blueprint, abort, g, redirect, render_template, request, url_for

from src.backend.dependencies.container import container

collection_bp = Blueprint("collection", __name__, url_prefix="/collections")


@collection_bp.route("", methods=["GET"])
def collections_page():
    """Рендерит страницу коллекций текущего пользователя."""
    user = getattr(g, "user", None)
    if not user:
        return redirect(url_for("auth.login_page"))
    collections = container.get_user_collections_use_case().execute(user.id)
    favorites = container.get_favorites_use_case().execute(user.id)
    return render_template(
        "collection/list.html",
        collections=collections,
        favorites=favorites,
    )


@collection_bp.route("", methods=["POST"])
def create_collection():
    """Создает новую коллекцию пользователя."""
    user = getattr(g, "user", None)
    if not user:
        abort(401)
    container.create_collection_use_case().execute(
        user_id=user.id,
        title=str(request.form.get("title") or "").strip(),
        description=str(request.form.get("description") or "").strip(),
        is_public=str(request.form.get("is_public") or "1").strip() in {"1", "true", "on"},
    )
    return redirect(url_for("collection.collections_page"))


@collection_bp.route("/<int:collection_id>/items", methods=["POST"])
def add_collection_item(collection_id: int):
    """Добавляет аниме в коллекцию пользователя."""
    user = getattr(g, "user", None)
    if not user:
        abort(401)
    genres = request.form.getlist("genres")
    if len(genres) == 1 and genres[0]:
        genres = [item.strip() for item in str(genres[0]).split(",") if item.strip()]
    container.add_collection_item_use_case().execute(
        collection_id=collection_id,
        anime_id=int(request.form.get("anime_id") or 0),
        title=str(request.form.get("title") or "").strip(),
        description=str(request.form.get("description") or "").strip(),
        cover_url=str(request.form.get("cover_url") or "").strip() or None,
        genres=genres,
    )
    return redirect(url_for("collection.collections_page"))


@collection_bp.route("/<int:collection_id>/items/remove", methods=["POST"])
def remove_collection_item(collection_id: int):
    """Удаляет аниме из коллекции пользователя."""
    user = getattr(g, "user", None)
    if not user:
        abort(401)
    container.remove_collection_item_use_case().execute(
        collection_id=collection_id,
        anime_id=int(request.form.get("anime_id") or 0),
    )
    return redirect(url_for("collection.collections_page"))


@collection_bp.route("/share/<int:collection_id>", methods=["GET"])
def shared_collection_page(collection_id: int):
    """Рендерит публичную share-страницу коллекции."""
    details = container.get_shared_collection_use_case().execute(collection_id)
    return render_template("collection/share.html", collection=details)
