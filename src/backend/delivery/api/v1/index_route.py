from flask import Blueprint, render_template, g
from src.backend.dependencies.container import container

index_bp = Blueprint("index", __name__, url_prefix="/")


@index_bp.route("/", methods=["GET"])
def index():
    """Главная страница"""
    popular_anime = container.get_season_popular_use_case().execute()
    recommendations = []
    user = g.user
    if user:
        recommendations = container.generate_recommendations_use_case().execute(
            user_id=user.id
        )

    return render_template(
        "index.html",
        popular_anime=popular_anime,
        recommendations=recommendations,
        current_user=user,
    )
