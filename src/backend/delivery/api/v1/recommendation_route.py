from flask import Blueprint, request, jsonify
from src.backend.dependencies.container import container
from src.backend.infrastructure.security.flask_protection import client_ip, rate_limit

recommendation_bp = Blueprint(
    "recommendation", __name__, url_prefix="/api/v1/recommendations"
)


@recommendation_bp.route("/generate/<int:user_id>", methods=["POST"])
@rate_limit(
    container_getter=lambda: container,
    scope="recommendation_generate",
    limit=20,
    window_seconds=60,
    key_builder=lambda: f"{client_ip()}::{request.view_args.get('user_id')}",
)
def generate_recommendations(user_id: int):
    results = container.generate_recommendations_use_case().execute(user_id=user_id)
    return jsonify([vars(r) for r in results])


@recommendation_bp.route("/refresh/<int:user_id>", methods=["POST"])
@rate_limit(
    container_getter=lambda: container,
    scope="recommendation_refresh",
    limit=10,
    window_seconds=60,
    key_builder=lambda: f"{client_ip()}::{request.view_args.get('user_id')}",
)
def refresh_recommendations(user_id: int):
    results = container.refresh_recommendations_use_case().execute(user_id=user_id)
    return jsonify([vars(r) for r in results])
