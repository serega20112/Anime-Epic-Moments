"""Тонкие HTTP-маршруты рекомендаций аниме."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends, Request

from backend.application.dto import RecommendationsQuery
from backend.application.use_cases import (
    AskAiRecommendationsUseCase,
    GenerateRecommendationsUseCase,
    RefreshRecommendationsUseCase,
)
from backend.application.use_cases.result import UseCaseResult
from backend.presentation.api.errors import ErrorResponse, error_from_result
from backend.presentation.api.rate_limit import client_ip, rate_limit
from backend.presentation.api.requests.recommendation_mapper import map_ask_ai_command
from backend.presentation.api.requests.recommendation_requests import AskAiRecommendationsRequest
from backend.presentation.api.responses.recommendation_responses import RecommendationItemResponse
from backend.presentation.api.version import API_PREFIX
from backend.presentation.dependencies.auth import require_self

recommendation_router = APIRouter(prefix=f"{API_PREFIX}/recommendations", route_class=DishkaRoute)

ERROR_RESPONSES = {
    "400": {"model": ErrorResponse},
    "401": {"model": ErrorResponse},
    "403": {"model": ErrorResponse},
    "429": {"model": ErrorResponse},
}


async def _recommendation_key(request: Request) -> str:
    """Собрать составной ключ ограничения частоты: IP и целевой пользователь.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        str: Ключ из адреса клиента и идентификатора пользователя из пути.
    """
    return f"{await client_ip(request)}::{request.path_params.get('user_id')}"


@recommendation_router.post(
    "/generate/{user_id}",
    name="recommendation.generate_recommendations",
    response_model=list[RecommendationItemResponse],
    responses=ERROR_RESPONSES,
)
@rate_limit(
    scope="recommendation_generate",
    limit=20,
    window_seconds=60,
    key_builder=_recommendation_key,
)
async def generate_recommendations(
    request: Request,
    user_id: int,
    use_case: FromDishka[GenerateRecommendationsUseCase],
    session_user_id: int = Depends(require_self),
) -> list:
    """Генерирует персональные рекомендации пользователя сессии.

    Args:
        request: Текущий HTTP-запрос, нужный ограничителю частоты.
        user_id: Идентификатор пользователя из пути.
        use_case: Сценарий генерации рекомендаций.
        session_user_id: Идентификатор пользователя сессии.

    Returns:
        list: Сериализованные рекомендации.

    Raises:
        HTTPException: 401 для анонимного запроса, 403 при чужом ``user_id``.
    """
    return await use_case.execute(RecommendationsQuery(user_id=session_user_id))


@recommendation_router.post(
    "/refresh/{user_id}",
    name="recommendation.refresh_recommendations",
    response_model=list[RecommendationItemResponse],
    responses=ERROR_RESPONSES,
)
@rate_limit(
    scope="recommendation_refresh",
    limit=10,
    window_seconds=60,
    key_builder=_recommendation_key,
)
async def refresh_recommendations(
    request: Request,
    user_id: int,
    use_case: FromDishka[RefreshRecommendationsUseCase],
    session_user_id: int = Depends(require_self),
) -> list:
    """Обновляет рекомендации пользователя сессии.

    Args:
        request: Текущий HTTP-запрос, нужный ограничителю частоты.
        user_id: Идентификатор пользователя из пути.
        use_case: Сценарий обновления рекомендаций.
        session_user_id: Идентификатор пользователя сессии.

    Returns:
        list: Сериализованные обновлённые рекомендации.

    Raises:
        HTTPException: 401 для анонимного запроса, 403 при чужом ``user_id``.
    """
    return await use_case.execute(RecommendationsQuery(user_id=session_user_id))


@recommendation_router.post(
    "/ask/{user_id}",
    name="recommendation.ask_ai_recommendations",
    response_model=list[RecommendationItemResponse],
    responses=ERROR_RESPONSES,
)
@rate_limit(
    scope="recommendation_ask_ai",
    limit=20,
    window_seconds=60,
    key_builder=_recommendation_key,
)
async def ask_ai_recommendations(
    request: Request,
    user_id: int,
    body: AskAiRecommendationsRequest,
    use_case: FromDishka[AskAiRecommendationsUseCase],
    session_user_id: int = Depends(require_self),
):
    """Подбирает аниме по свободному текстовому запросу к LLM.

    Сценарий платный: обращение к модели допускается только от имени
    пользователя сессии, иначе чужой ``user_id`` в пути позволял бы тратить
    квоту владельца и получать подбор по его избранному.

    Args:
        request: Текущий HTTP-запрос, нужный ограничителю частоты.
        user_id: Идентификатор пользователя из пути.
        body: Проверенное тело запроса к ИИ.
        use_case: Сценарий AI-рекомендаций.
        session_user_id: Идентификатор пользователя сессии.

    Returns:
        list | Response: Рекомендации либо тело ошибки сценария.

    Raises:
        HTTPException: 401 для анонимного запроса, 403 при чужом ``user_id``.
    """
    result: UseCaseResult = await use_case.execute(
        map_ask_ai_command(body, user_id=session_user_id)
    )
    if not result.ok:
        return error_from_result(result)
    return result.data
