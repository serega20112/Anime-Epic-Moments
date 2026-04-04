from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.backend.delivery.api.helpers import get_container, read_payload
from src.backend.infrastructure.security.flask_protection import client_ip, rate_limit

recommendation_router = APIRouter(prefix="/api/v1/recommendations")
recommendation_bp = recommendation_router
container = None


@recommendation_router.post("/generate/{user_id}", name="recommendation.generate_recommendations")
@rate_limit(
    scope="recommendation_generate",
    limit=20,
    window_seconds=60,
    key_builder=lambda request: f"{client_ip(request)}::{request.path_params.get('user_id')}",
)
async def generate_recommendations(request: Request, user_id: int):
    container = get_container(request)
    results = await container.generate_recommendations_use_case().execute(user_id=user_id)
    return [vars(item) for item in results]


@recommendation_router.post("/refresh/{user_id}", name="recommendation.refresh_recommendations")
@rate_limit(
    scope="recommendation_refresh",
    limit=10,
    window_seconds=60,
    key_builder=lambda request: f"{client_ip(request)}::{request.path_params.get('user_id')}",
)
async def refresh_recommendations(request: Request, user_id: int):
    container = get_container(request)
    results = await container.refresh_recommendations_use_case().execute(user_id=user_id)
    return [vars(item) for item in results]


@recommendation_router.post("/ask/{user_id}", name="recommendation.ask_ai_recommendations")
@rate_limit(
    scope="recommendation_ask_ai",
    limit=20,
    window_seconds=60,
    key_builder=lambda request: f"{client_ip(request)}::{request.path_params.get('user_id')}",
)
async def ask_ai_recommendations(request: Request, user_id: int):
    container = get_container(request)
    payload = await read_payload(request)
    query = str(payload.get("query") or "").strip()
    limit = payload.get("limit", 6)
    try:
        limit = max(1, min(int(limit), 10))
    except (TypeError, ValueError):
        limit = 6
    if not query:
        return JSONResponse({"error": "invalid_query"}, status_code=400)
    results = await container.ask_ai_recommendations_use_case().execute(
        user_id=user_id,
        query=query,
        limit=limit,
    )
    return [vars(item) for item in results]
