"""JSON-маршруты отметок прочтения уведомлений пользователя сессии."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.dto.notification import (
    MarkAllNotificationsReadCommand,
    MarkNotificationReadCommand,
)
from backend.application.use_cases.notification import (
    MarkAllNotificationsReadUseCase,
    MarkNotificationReadUseCase,
)
from backend.presentation.api.errors import unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.responses.notification_responses import (
    NotificationsMarkedResponse,
)
from backend.presentation.api.v1.watch_route.helpers import ERROR_RESPONSES
from backend.presentation.api.version import API_PREFIX

actions_router = APIRouter(prefix=f"{API_PREFIX}/notifications", route_class=DishkaRoute)


@actions_router.post(
    "/{notification_id}/read",
    name="api_notifications.mark_read",
    response_model=NotificationsMarkedResponse,
    responses=ERROR_RESPONSES,
)
async def mark_read(
    request: Request,
    notification_id: int,
    use_case: FromDishka[MarkNotificationReadUseCase],
):
    """Отметить одно уведомление прочитанным.

    Args:
        request: Текущий HTTP-запрос с заголовком Authorization.
        notification_id: Идентификатор уведомления из пути.
        use_case: Сценарий отметки прочтения.

    Returns:
        NotificationsMarkedResponse | Response: Число изменений либо отказ 401.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    marked = await use_case.execute(
        MarkNotificationReadCommand(user_id=user.id, notification_id=notification_id)
    )
    return NotificationsMarkedResponse(marked=marked)


@actions_router.post(
    "/read-all",
    name="api_notifications.mark_all_read",
    response_model=NotificationsMarkedResponse,
    responses=ERROR_RESPONSES,
)
async def mark_all_read(
    request: Request,
    use_case: FromDishka[MarkAllNotificationsReadUseCase],
):
    """Отметить все уведомления пользователя прочитанными.

    Args:
        request: Текущий HTTP-запрос с заголовком Authorization.
        use_case: Сценарий массового прочтения.

    Returns:
        NotificationsMarkedResponse | Response: Число изменений либо отказ 401.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    marked = await use_case.execute(MarkAllNotificationsReadCommand(user_id=user.id))
    return NotificationsMarkedResponse(marked=marked)
