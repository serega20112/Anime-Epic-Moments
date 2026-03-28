from flask import Blueprint, request, render_template, abort
from src.backend.dependencies.container import container

favorite_bp = Blueprint("favorite", __name__, url_prefix="/favorites")


def _extract_favorite_payload():
    """Извлекает user_id, anime_id и snapshot-метаданные из JSON или form-data."""
    payload = request.get_json(silent=True) or {}
    return {
        "user_id": payload.get("user_id", request.form.get("user_id")),
        "anime_id": payload.get("anime_id", request.form.get("anime_id")),
        "title": payload.get("title", request.form.get("title")),
        "description": payload.get("description", request.form.get("description")),
        "cover_url": payload.get("cover_url", request.form.get("cover_url")),
        "genres": payload.get("genres", request.form.get("genres")),
    }


@favorite_bp.route("/", methods=["POST"])
def add_favorite():
    """Добавление аниме в избранное пользователя"""
    favorite_payload = _extract_favorite_payload()
    user_id = favorite_payload["user_id"]
    anime_id = favorite_payload["anime_id"]
    if user_id is None or anime_id is None:
        abort(400)
    container.add_favorite_use_case().execute(**favorite_payload)
    return "", 201


@favorite_bp.route("/", methods=["DELETE"])
def remove_favorite():
    """Удаление аниме из избранного пользователя"""
    favorite_payload = _extract_favorite_payload()
    user_id = favorite_payload["user_id"]
    anime_id = favorite_payload["anime_id"]
    if user_id is None or anime_id is None:
        abort(400)
    container.remove_favorite_use_case().execute(user_id=user_id, anime_id=anime_id)
    return "", 204


@favorite_bp.route("/<int:user_id>", methods=["GET"])
def get_favorites(user_id: int):
    """Рендер страницы с избранным пользователя"""
    favorites = container.get_favorites_use_case().execute(user_id=user_id)
    recommendations = container.generate_recommendations_use_case().execute(
        user_id=user_id
    )
    return render_template(
        "favorite/list.html",
        favorites=favorites,
        recommendations=recommendations,
        user_id=user_id,
    )
