"""Thin HTTP routes for anime recommendations."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from backend.application.use_cases import AskAiRecommendationsUseCase
from backend.application.use_cases import GenerateRecommendationsUseCase
from backend.application.use_cases import RefreshRecommendationsUseCase
from backend.presentation.api.requests.recommendation_mapper import map_ask_ai_command

from backend.infrastructure.security.flask_protection import client_ip, rate_limit
from backend.presentation.api.helpers import read_payload

recommendation_router = APIRouter(prefix="/api/v1/recommendations", route_class=DishkaRoute)
recommendation_bp = recommendation_router


@recommendation_router.post("/generate/{user_id}", name="recommendation.generate_recommendations")
@rate_limit(
    scope="recommendation_generate",
    limit=20,
    window_seconds=60,
    key_builder=lambda request: f"{client_ip(request)}::{request.path_params.get('user_id')}",
)
async def generate_recommendations(
        request: Request,
        user_id: int,
        use_case: FromDishka[GenerateRecommendationsUseCase],
):
    """Generate personalized recommendations for a user.

    Args:
        request: Incoming HTTP request.
        user_id: User ID from path.
        use_case: Generate recommendations use case.

    Returns:
        JSONResponse: Serialized recommendation results.
    """
    results = await use_case.execute(user_id=user_id)
    return JSONResponse(content=[vars(item) for item in results])


@recommendation_router.post("/refresh/{user_id}", name="recommendation.refresh_recommendations")
@rate_limit(
    scope="recommendation_refresh",
    limit=10,
    window_seconds=60,
    key_builder=lambda request: f"{client_ip(request)}::{request.path_params.get('user_id')}",
)
async def refresh_recommendations(
        request: Request,
        user_id: int,
        use_case: FromDishka[RefreshRecommendationsUseCase],
):
    """Refresh recommendations for a user.

    Args:
        request: Incoming HTTP request.
        user_id: User ID from path.
        use_case: Refresh recommendations use case.

    Returns:
        JSONResponse: Serialized refreshed recommendations.
    """
    results = await use_case.execute(user_id=user_id)
    return JSONResponse(content=[vars(item) for item in results])


@recommendation_router.post("/ask/{user_id}", name="recommendation.ask_ai_recommendations")
@rate_limit(
    scope="recommendation_ask_ai",
    limit=20,
    window_seconds=60,
    key_builder=lambda request: f"{client_ip(request)}::{request.path_params.get('user_id')}",
)
async def ask_ai_recommendations(
        request: Request,
        user_id: int,
        use_case: FromDishka[AskAiRecommendationsUseCase],
):
    """Recommend anime from a free-form AI query.

    Args:
        request: Incoming HTTP request.
        user_id: User ID from path.
        use_case: Ask AI recommendations use case.

    Returns:
        JSONResponse: Serialized recommendations or an error payload.
    """
    command = map_ask_ai_command(await read_payload(request), user_id=user_id)
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return JSONResponse(
        content=[vars(item) for item in result.data],
        status_code=result.status_code,
    )
