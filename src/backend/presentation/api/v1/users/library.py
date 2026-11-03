"""JSON-маршруты дневника просмотра и истории для мобильного клиента.

Маршруты читают приватный дневник пользователя: идентификатор из пути сверяется
с сессией через ``require_self``, а карточки собирают существующие сценарии
чтения. Нарезку на страницы сценарии пока не поддерживают, поэтому вся выборка
идёт одной страницей через общий конверт пагинации.
"""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from backend.application.dto.watch import GetUserHistoryQuery, GetUserLibraryQuery
from backend.application.use_cases import (
    GetUserAnimeLibraryUseCase,
    GetUserViewingHistoryUseCase,
)
from backend.presentation.api.responses.pagination import as_single_page
from backend.presentation.api.responses.watch_responses import (
    HistoryEntryResponse,
    HistoryPageResponse,
    LibraryEntryResponse,
    LibraryPageResponse,
)
from backend.presentation.api.v1.users.helpers import OWNER_ERROR_RESPONSES
from backend.presentation.dependencies.auth import require_self

library_router = APIRouter(route_class=DishkaRoute)


@library_router.get(
    "/{user_id}/library",
    name="api_users.get_library_all",
    response_model=LibraryPageResponse,
    responses=OWNER_ERROR_RESPONSES,
)
async def get_library_all(
    user_id: int,
    use_case: FromDishka[GetUserAnimeLibraryUseCase],
    session_user_id: int = Depends(require_self),
):
    """Вернуть весь дневник просмотра пользователя сессии.

    Args:
        user_id: Идентификатор пользователя из пути.
        use_case: Сценарий чтения библиотеки.
        session_user_id: Идентификатор пользователя сессии.

    Returns:
        LibraryPageResponse: Карточки дневника одной страницей.

    Raises:
        HTTPException: 401 для анонимного запроса, 403 при чужом ``user_id``.
    """
    cards = await use_case.execute(GetUserLibraryQuery(user_id=session_user_id))
    return LibraryPageResponse(**as_single_page([_library_entry(card) for card in cards]))


@library_router.get(
    "/{user_id}/library/{status}",
    name="api_users.get_library_by_status",
    response_model=LibraryPageResponse,
    responses=OWNER_ERROR_RESPONSES,
)
async def get_library_by_status(
    user_id: int,
    status: str,
    use_case: FromDishka[GetUserAnimeLibraryUseCase],
    session_user_id: int = Depends(require_self),
):
    """Вернуть дневник просмотра пользователя, отфильтрованный по статусу.

    Args:
        user_id: Идентификатор пользователя из пути.
        status: Требуемый статус дневника из пути.
        use_case: Сценарий чтения библиотеки.
        session_user_id: Идентификатор пользователя сессии.

    Returns:
        LibraryPageResponse: Карточки выбранного статуса одной страницей.

    Raises:
        HTTPException: 401 для анонимного запроса, 403 при чужом ``user_id``.
    """
    cards = await use_case.execute(GetUserLibraryQuery(user_id=session_user_id, status=status))
    return LibraryPageResponse(**as_single_page([_library_entry(card) for card in cards]))


@library_router.get(
    "/{user_id}/history",
    name="api_users.get_history",
    response_model=HistoryPageResponse,
    responses=OWNER_ERROR_RESPONSES,
)
async def get_history(
    user_id: int,
    use_case: FromDishka[GetUserViewingHistoryUseCase],
    session_user_id: int = Depends(require_self),
):
    """Вернуть историю просмотров пользователя сессии.

    Args:
        user_id: Идентификатор пользователя из пути.
        use_case: Сценарий чтения истории.
        session_user_id: Идентификатор пользователя сессии.

    Returns:
        HistoryPageResponse: Карточки последних сессий одной страницей.

    Raises:
        HTTPException: 401 для анонимного запроса, 403 при чужом ``user_id``.
    """
    cards = await use_case.execute(GetUserHistoryQuery(user_id=session_user_id))
    return HistoryPageResponse(**as_single_page([_history_entry(card) for card in cards]))


def _library_entry(card) -> LibraryEntryResponse:
    """Превратить доменную карточку библиотеки в ответ маршрута.

    Args:
        card: Доменная карточка :class:`LibraryAnimeCard`.

    Returns:
        LibraryEntryResponse: JSON-представление записи дневника.
    """
    return LibraryEntryResponse.model_validate(card)


def _history_entry(card) -> HistoryEntryResponse:
    """Превратить доменную карточку истории в ответ маршрута.

    Args:
        card: Доменная карточка :class:`HistoryAnimeCard`.

    Returns:
        HistoryEntryResponse: JSON-представление записи истории.
    """
    return HistoryEntryResponse.model_validate(card)
