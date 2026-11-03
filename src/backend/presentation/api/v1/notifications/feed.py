"""JSON-маршрут выдачи ленты уведомлений пользователя сессии."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.dto.notification import NotificationsQuery
from backend.application.use_cases.notification import GetUserNotificationsUseCase
from backend.domain import NotificationFeedPage
from backend.presentation.api.errors import unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.responses.notification_responses import (
    NotificationResponse,
    NotificationsPageResponse,
)
from backend.presentation.api.v1.watch_route.helpers import ERROR_RESPONSES
from backend.presentation.api.version import API_PREFIX

feed_router = APIRouter(prefix=f"{API_PREFIX}/notifications", route_class=DishkaRoute)

DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20


@feed_router.get(
    "",
    name="api_notifications.list",
    response_model=NotificationsPageResponse,
    responses=ERROR_RESPONSES,
)
async def list_notifications(
    request: Request,
    use_case: FromDishka[GetUserNotificationsUseCase],
):
    """Отдать страницу уведомлений пользователя сессии.

    Args:
        request: Текущий HTTP-запрос с параметрами страницы.
        use_case: Сценарий чтения уведомлений.

    Returns:
        NotificationsPageResponse | Response: Страница уведомлений либо отказ 401.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    params = request.query_params
    page = await use_case.execute(
        NotificationsQuery(
            user_id=user.id,
            page=_positive_int(params.get("page"), DEFAULT_PAGE),
            per_page=_positive_int(params.get("per_page"), DEFAULT_PER_PAGE),
        )
    )
    return _to_page_response(page)


def _to_page_response(page: NotificationFeedPage) -> NotificationsPageResponse:
    """Превратить доменную страницу уведомлений в ответ маршрута.

    Args:
        page: Доменная страница уведомлений с именами авторов.

    Returns:
        NotificationsPageResponse: JSON-страница с навигацией и счётчиком.
    """
    return NotificationsPageResponse(
        items=[
            NotificationResponse(
                id=item.id or 0,
                kind=item.kind,
                text=item.text,
                actor_user_id=item.actor_user_id,
                actor_name=page.actor_names.get(item.actor_user_id)
                if item.actor_user_id is not None
                else None,
                anime_id=item.anime_id,
                highlight_id=item.highlight_id,
                is_read=item.is_read,
                created_at=item.created_at,
            )
            for item in page.items
        ],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        total_pages=max(1, -(-page.total // page.per_page)),
        has_next=page.page * page.per_page < page.total,
        has_previous=page.page > 1,
        unread_count=page.unread_count,
    )


def _positive_int(value: str | None, default: int) -> int:
    """Разобрать положительный параметр строки запроса.

    Args:
        value: Сырое значение параметра.
        default: Значение при отсутствии или нечисловом вводе.

    Returns:
        int: Целое не меньше единицы либо значение по умолчанию.
    """
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 1 else default
