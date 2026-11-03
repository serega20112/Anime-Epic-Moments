"""JSON-маршруты списка и создания коллекций пользователя сессии.

Оба маршрута приватны: идентификатор из пути сверяется с сессией через
``require_self``, а карточки собирает существующий сценарий чтения. Модель ответа
строится из доменных карточек; решений о выборке в маршрутах нет.
"""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from backend.application.dto import (
    CreateCollectionCommand,
    GetUserCollectionsQuery,
)
from backend.application.use_cases import (
    CreateCollectionUseCase,
    GetUserCollectionsUseCase,
)
from backend.presentation.api.responses.collection_responses import (
    MobileCollectionResponse,
    MobileCollectionsResponse,
)
from backend.presentation.api.v1.collections.helpers import OWNER_ERROR_RESPONSES
from backend.presentation.api.version import API_PREFIX
from backend.presentation.dependencies.auth import require_self

user_collections_router = APIRouter(prefix=f"{API_PREFIX}/users", route_class=DishkaRoute)

COLLECTION_TITLE_MAX_LENGTH = 80
COLLECTION_DESCRIPTION_MAX_LENGTH = 400


class MobileCreateCollectionRequest(BaseModel):
    """Тело создания коллекции мобильным клиентом.

    Attributes:
        title: Название коллекции.
        description: Описание коллекции.
        is_public: Делать ли коллекцию публичной.
        cover_url: Ссылка на обложку либо None.
    """

    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1, max_length=COLLECTION_TITLE_MAX_LENGTH)
    description: str = Field(default="", max_length=COLLECTION_DESCRIPTION_MAX_LENGTH)
    is_public: bool = True
    cover_url: str | None = Field(default=None, max_length=500)


@user_collections_router.get(
    "/{user_id}/collections",
    name="api_collections.list",
    response_model=MobileCollectionsResponse,
    responses=OWNER_ERROR_RESPONSES,
)
async def list_collections(
    user_id: int,
    use_case: FromDishka[GetUserCollectionsUseCase],
    session_user_id: int = Depends(require_self),
):
    """Вернуть коллекции пользователя сессии.

    Args:
        user_id: Идентификатор пользователя из пути.
        use_case: Сценарий списка коллекций.
        session_user_id: Идентификатор пользователя сессии.

    Returns:
        MobileCollectionsResponse: Карточки коллекций владельца сессии.

    Raises:
        HTTPException: 401 для анонимного запроса, 403 при чужом ``user_id``.
    """
    details = await use_case.execute(GetUserCollectionsQuery(user_id=session_user_id))
    return MobileCollectionsResponse(
        items=[_collection_card(item.collection, session_user_id) for item in details]
    )


@user_collections_router.post(
    "/{user_id}/collections",
    name="api_collections.create",
    response_model=MobileCollectionResponse,
    status_code=HTTPStatus.CREATED,
    responses=OWNER_ERROR_RESPONSES,
)
async def create_collection(
    user_id: int,
    body: MobileCreateCollectionRequest,
    use_case: FromDishka[CreateCollectionUseCase],
    session_user_id: int = Depends(require_self),
):
    """Создать коллекцию пользователя сессии.

    Args:
        user_id: Идентификатор пользователя из пути.
        body: Проверенное тело новой коллекции.
        use_case: Сценарий создания коллекции.
        session_user_id: Идентификатор пользователя сессии.

    Returns:
        MobileCollectionResponse: Карточка созданной коллекции.

    Raises:
        HTTPException: 401 для анонимного запроса, 403 при чужом ``user_id``.
    """
    collection = await use_case.execute(
        CreateCollectionCommand(
            user_id=session_user_id,
            title=body.title.strip(),
            description=body.description.strip(),
            is_public=body.is_public,
            cover_url=body.cover_url,
        )
    )
    return MobileCollectionResponse(
        id=collection.id or 0,
        title=collection.title,
        is_public=collection.is_public,
        item_count=0,
        cover_url=collection.cover_url,
        owner_id=session_user_id,
    )


def _collection_card(collection, owner_id: int) -> MobileCollectionResponse:
    """Собрать мобильную карточку коллекции из доменной карточки.

    Args:
        collection: Доменная карточка коллекции со счётчиком элементов.
        owner_id: Идентификатор владельца коллекции из сессии.

    Returns:
        MobileCollectionResponse: JSON-представление коллекции.
    """
    return MobileCollectionResponse(
        id=collection.id,
        title=collection.title,
        is_public=collection.is_public,
        item_count=collection.items_count,
        cover_url=collection.cover_url,
        owner_id=owner_id,
    )
