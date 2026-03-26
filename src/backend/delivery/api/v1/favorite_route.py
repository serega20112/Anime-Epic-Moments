from flask import Blueprint, request, render_template, abort
from src.backend.dependencies.container import container

favorite_bp = Blueprint("favorite", __name__, url_prefix="/favorites")


def _extract_favorite_payload():
    """Извлекает user_id и anime_id из JSON или form-data."""
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id", request.form.get("user_id"))
    anime_id = payload.get("anime_id", request.form.get("anime_id"))
    return user_id, anime_id

@favorite_bp.route("/", methods=["POST"])
def add_favorite():
    """Добавление аниме в избранное пользователя"""
    user_id, anime_id = _extract_favorite_payload()
    if user_id is None or anime_id is None:
        abort(400)
    container.add_favorite_use_case().execute(
        user_id=user_id,
        anime_id=anime_id
    )
    return "", 201

@favorite_bp.route("/", methods=["DELETE"])
def remove_favorite():
    """Удаление аниме из избранного пользователя"""
    user_id, anime_id = _extract_favorite_payload()
    if user_id is None or anime_id is None:
        abort(400)
    container.remove_favorite_use_case().execute(
        user_id=user_id,
        anime_id=anime_id
    )
    return "", 204

@favorite_bp.route("/<int:user_id>", methods=["GET"])
def get_favorites(user_id: int):
    """Рендер страницы с избранным пользователя"""
    favorites = container.get_favorites_use_case().execute(user_id=user_id)
    recommendations = container.generate_recommendations_use_case().execute(user_id=user_id)
    return render_template("favorite/list.html", favorites=favorites, recommendations=recommendations, user_id=user_id)
