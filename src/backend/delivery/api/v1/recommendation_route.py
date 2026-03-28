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


@recommendation_bp.route("/ask/<int:user_id>", methods=["POST"])
@rate_limit(
    container_getter=lambda: container,
    scope="recommendation_ask_ai",
    limit=20,
    window_seconds=60,
    key_builder=lambda: f"{client_ip()}::{request.view_args.get('user_id')}",
)
def ask_ai_recommendations(user_id: int):
    payload = request.get_json(silent=True) or {}
    query = str(payload.get("query") or "").strip()
    limit = payload.get("limit", 6)
    try:
        limit = max(1, min(int(limit), 10))
    except (TypeError, ValueError):
        limit = 6
    if not query:
        return jsonify({"error": "invalid_query"}), 400
    results = container.ask_ai_recommendations_use_case().execute(
        user_id=user_id,
        query=query,
        limit=limit,
    )
    return jsonify([vars(r) for r in results])
