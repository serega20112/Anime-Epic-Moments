"""JSON-маршрут публичного профиля пользователя для мобильного клиента."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.dto.user import PublicProfileQuery
from backend.application.use_cases import GetPublicProfileOverviewUseCase
from backend.presentation.api.errors import ErrorResponse, error_from_result
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.responses.user_responses import MobileProfileResponse

profile_router = APIRouter(route_class=DishkaRoute)


@profile_router.get(
    "/{user_id}",
    name="api_users.profile",
    response_model=MobileProfileResponse,
    responses={HTTPStatus.NOT_FOUND: {"model": ErrorResponse}},
)
async def get_profile(
    request: Request,
    user_id: int,
    use_case: FromDishka[GetPublicProfileOverviewUseCase],
):
    """Вернуть публичный профиль пользователя.

    Зритель определяется по сессии или Bearer-токену: только он влияет на поле
    ``is_followed``. Чужой профиль остаётся доступен гостю.

    Args:
        request: Текущий HTTP-запрос.
        user_id: Идентификатор открываемого профиля.
        use_case: Сценарий обзора публичного профиля.

    Returns:
        MobileProfileResponse | Response: Профиль либо тело отказа 404.
    """
    viewer = await get_current_user(request)
    result = await use_case.execute(
        PublicProfileQuery(profile_user_id=user_id, viewer_user_id=viewer.id if viewer else None)
    )
    if not result.ok:
        return error_from_result(result)
    return _build_profile_response(result.data)


def _build_profile_response(overview) -> MobileProfileResponse:
    """Собрать ответ профиля из обзора публичного профиля.

    Args:
        overview: Доменный обзор публичного профиля с социальными счётчиками.

    Returns:
        MobileProfileResponse: JSON-представление профиля без приватной почты.
    """
    profile = overview.profile
    return MobileProfileResponse(
        id=profile.user_id,
        username=profile.username,
        avatar_url=profile.avatar_url,
        bio=profile.status,
        highlights_count=profile.summary.highlight_count,
        followers_count=overview.followers_count,
        following_count=overview.following_count,
        is_followed=overview.is_following,
    )
