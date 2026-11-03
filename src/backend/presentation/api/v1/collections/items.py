"""JSON-маршруты элементов коллекции мобильного клиента.

Добавление и удаление элемента выполняются от имени пользователя сессии, а
право владельца на конкретную коллекцию проверяет сценарий — в маршруте решений
о доступе нет.
"""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import Response

from backend.application.dto import (
    AddCollectionItemCommand,
    RemoveCollectionItemCommand,
)
from backend.application.use_cases import (
    AddCollectionItemUseCase,
    RemoveCollectionItemUseCase,
)
from backend.presentation.api.errors import unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.collection_requests import (
    AddCollectionItemRequest,
    RemoveCollectionItemRequest,
)
from backend.presentation.api.responses.collection_responses import (
    CollectionItemAddedResponse,
)
from backend.presentation.api.v1.collections.helpers import OWNER_ERROR_RESPONSES
from backend.presentation.api.version import API_PREFIX

items_router = APIRouter(prefix=f"{API_PREFIX}/collections", route_class=DishkaRoute)


@items_router.post(
    "/{collection_id}/items",
    name="api_collections.add_item",
    response_model=CollectionItemAddedResponse,
    status_code=HTTPStatus.CREATED,
    responses=OWNER_ERROR_RESPONSES,
)
async def add_item(
    request: Request,
    collection_id: int,
    body: AddCollectionItemRequest,
    use_case: FromDishka[AddCollectionItemUseCase],
):
    """Добавить аниме в коллекцию владельца сессии.

    Args:
        request: Текущий HTTP-запрос.
        collection_id: Идентификатор коллекции из пути.
        body: Тело запроса с идентификатором аниме.
        use_case: Сценарий добавления элемента коллекции.

    Returns:
        CollectionItemAddedResponse | Response: Итог добавления либо отказ
            401/403 через общий обработчик.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    await use_case.execute(
        AddCollectionItemCommand(
            collection_id=collection_id, anime_id=body.anime_id, user_id=user.id
        )
    )
    return CollectionItemAddedResponse(
        collection_id=collection_id, anime_id=body.anime_id, added=True
    )


@items_router.post(
    "/{collection_id}/items/remove",
    name="api_collections.remove_item",
    status_code=HTTPStatus.NO_CONTENT,
    responses=OWNER_ERROR_RESPONSES,
)
async def remove_item(
    request: Request,
    collection_id: int,
    body: RemoveCollectionItemRequest,
    use_case: FromDishka[RemoveCollectionItemUseCase],
):
    """Убрать аниме из коллекции владельца сессии.

    Args:
        request: Текущий HTTP-запрос.
        collection_id: Идентификатор коллекции из пути.
        body: Тело запроса с идентификатором аниме.
        use_case: Сценарий удаления элемента коллекции.

    Returns:
        Response: 204 при успехе либо отказ 401/403 через общий обработчик.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    await use_case.execute(
        RemoveCollectionItemCommand(
            collection_id=collection_id,
            anime_id=body.anime_id,
            user_id=user.id,
        )
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)
