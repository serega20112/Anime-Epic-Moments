from flask import Blueprint, request, jsonify
from src.backend.dependencies.container import container

recommendation_bp = Blueprint("recommendation", __name__, url_prefix="/api/v1/recommendations")


@recommendation_bp.route("/generate/<int:user_id>", methods=["POST"])
def generate_recommendations(user_id: int):
    results = container.generate_recommendations_use_case().execute(user_id=user_id)
    return jsonify([vars(r) for r in results])


@recommendation_bp.route("/refresh/<int:user_id>", methods=["POST"])
def refresh_recommendations(user_id: int):
    results = container.refresh_recommendations_use_case().execute(user_id=user_id)
    return jsonify([vars(r) for r in results])