"""JSON-маршруты выгрузки данных и удаления аккаунта мобильного клиента.

Оба маршрута приватны: идентификатор из пути сверяется с сессией через
``require_self``. Решение о каскаде удаления и составе выгрузки принимает
сценарий; маршрут читает итог и оформляет ответ.
"""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from backend.application.dto.account import DeleteAccountCommand, ExportUserDataQuery
from backend.application.use_cases import DeleteAccountUseCase, ExportUserDataUseCase
from backend.presentation.api.errors import error_from_result
from backend.presentation.api.responses.account_responses import (
    AccountDeletedResponse,
    AccountExportResponse,
)
from backend.presentation.api.v1.users.helpers import OWNER_ERROR_RESPONSES
from backend.presentation.dependencies.auth import require_self

account_router = APIRouter(route_class=DishkaRoute)


@account_router.get(
    "/{user_id}/export",
    name="api_users.export_data",
    response_model=AccountExportResponse,
    responses=OWNER_ERROR_RESPONSES,
)
async def export_data(
    user_id: int,
    use_case: FromDishka[ExportUserDataUseCase],
    session_user_id: int = Depends(require_self),
):
    """Вернуть машиночитаемую копию данных пользователя сессии.

    Args:
        user_id: Идентификатор пользователя из пути.
        use_case: Сценарий выгрузки данных.
        session_user_id: Идентификатор пользователя сессии.

    Returns:
        dict | Response: Разделы выгрузки либо тело отказа.

    Raises:
        HTTPException: 401 для анонимного запроса, 403 при чужом ``user_id``.
    """
    result = await use_case.execute(ExportUserDataQuery(user_id=session_user_id))
    if not result.ok:
        return error_from_result(result)
    return result.data


@account_router.delete(
    "/{user_id}",
    name="api_users.delete_account",
    response_model=AccountDeletedResponse,
    responses=OWNER_ERROR_RESPONSES,
)
async def delete_account(
    user_id: int,
    use_case: FromDishka[DeleteAccountUseCase],
    session_user_id: int = Depends(require_self),
):
    """Удалить аккаунт пользователя сессии вместе со всеми его данными.

    Args:
        user_id: Идентификатор пользователя из пути.
        use_case: Сценарий удаления аккаунта.
        session_user_id: Идентификатор пользователя сессии.

    Returns:
        AccountDeletedResponse | Response: Признак удаления либо тело отказа.

    Raises:
        HTTPException: 401 для анонимного запроса, 403 при чужом ``user_id``.
    """
    result = await use_case.execute(DeleteAccountCommand(user_id=session_user_id))
    if not result.ok:
        return error_from_result(result)
    return AccountDeletedResponse(deleted=result.data["deleted"])
