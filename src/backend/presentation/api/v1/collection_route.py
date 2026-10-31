"""Тонкие HTTP-маршруты управления коллекциями аниме."""

from __future__ import annotations

from dataclasses import replace
from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, Response

from backend.application.dto import (
    AddCollectionItemCommand,
    GetFavoritesQuery,
    GetSharedCollectionQuery,
    GetUserCollectionsQuery,
    RemoveCollectionItemCommand,
)
from backend.application.interface.services import ImageStorageError, ImageStoragePort
from backend.application.use_cases import (
    AddCollectionItemUseCase,
    CreateCollectionUseCase,
    GetFavoritesUseCase,
    GetUserCollectionsUseCase,
    RemoveCollectionItemUseCase,
)
from backend.application.use_cases.collection.add_collection_item import CollectionAccessError
from backend.application.use_cases.collection.get_shared_collection import (
    GetSharedCollectionUseCase,
)
from backend.presentation.api.errors import ErrorResponse, unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.collection_mapper import (
    map_create_collection_command,
)
from backend.presentation.api.requests.collection_requests import (
    AddCollectionItemRequest,
    RemoveCollectionItemRequest,
)
from backend.presentation.api.requests.form_models import read_form_model
from backend.presentation.api.responses.collection_responses import (
    CollectionSummaryResponse,
    MyCollectionsResponse,
)
from backend.presentation.web import flash, render_template

collection_router = APIRouter(prefix="/collections", route_class=DishkaRoute)


@collection_router.get("", name="collection.collections_page")
async def collections_page(
    request: Request,
    collections_use_case: FromDishka[GetUserCollectionsUseCase],
    favorites_use_case: FromDishka[GetFavoritesUseCase],
):
    """Отдать страницу коллекций и избранного пользователя.

    Args:
        request: Текущий HTTP-запрос.
        collections_use_case: Сценарий списка коллекций.
        favorites_use_case: Сценарий списка избранного.

    Returns:
        Response: Страница коллекций либо редирект гостя на вход.
    """
    user = await get_current_user(request)
    if not user:
        return redirect_login(request)
    collections = await collections_use_case.execute(GetUserCollectionsQuery(user_id=user.id))
    favorites = await favorites_use_case.execute(GetFavoritesQuery(user_id=user.id))
    return await render_template(
        request,
        "collection/list.html",
        collections=collections,
        favorites=favorites,
    )


@collection_router.post("", name="collection.create_collection")
async def create_collection(
    request: Request,
    use_case: FromDishka[CreateCollectionUseCase],
    storage: FromDishka[ImageStoragePort],
):
    """Создаёт коллекцию по данным формы.

    Обложка берётся из загруженного файла, если он есть, иначе из поля
    ``cover_url``; загруженные файлы хранит порт хранилища изображений.

    Args:
        request: Текущий HTTP-запрос с формой.
        use_case: Сценарий создания коллекции.
        storage: Хранилище загруженной обложки.

    Returns:
        Response: 401 для гостя.
        RedirectResponse: Редирект на страницу коллекций.
    """
    user = await get_current_user(request)
    if not user:
        return Response(status_code=HTTPStatus.UNAUTHORIZED)
    form = await request.form()
    cover_url = str(form.get("cover_url") or "").strip() or None
    cover_file = form.get("cover_file")
    if cover_file is not None and getattr(cover_file, "filename", None):
        try:
            cover_url = await storage.save(cover_file, "covers")
        except ImageStorageError as error:
            await flash(request, str(error))
            return redirect_collections(request)
    command = replace(map_create_collection_command(form, user_id=user.id), cover_url=cover_url)
    try:
        await use_case.execute(command)
    except ValueError as error:
        await flash(request, str(error))
    return redirect_collections(request)


@collection_router.post(
    "/{collection_id}/items",
    name="collection.add_collection_item",
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.BAD_REQUEST: {"model": ErrorResponse},
        HTTPStatus.FORBIDDEN: {"model": ErrorResponse},
        HTTPStatus.UNAUTHORIZED: {"model": ErrorResponse},
    },
)
async def add_collection_item(
    request: Request,
    collection_id: int,
    body: AddCollectionItemRequest,
    use_case: FromDishka[AddCollectionItemUseCase],
):
    """Добавляет аниме в коллекцию владельца сессии.

    Args:
        request: Текущий HTTP-запрос.
        collection_id: Идентификатор коллекции из пути.
        body: Тело запроса с идентификатором аниме.
        use_case: Сценарий добавления элемента коллекции.

    Returns:
        Response: 201 при успехе, 401/403/400 через общий обработчик ошибок.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    await use_case.execute(
        AddCollectionItemCommand(
            collection_id=collection_id,
            anime_id=body.anime_id,
            user_id=user.id,
        )
    )
    return Response(status_code=HTTPStatus.CREATED)


@collection_router.post(
    "/{collection_id}/items/remove",
    name="collection.remove_collection_item",
)
async def remove_collection_item(
    request: Request,
    collection_id: int,
    use_case: FromDishka[RemoveCollectionItemUseCase],
):
    """Убирает аниме из коллекции.

    Args:
        request: Текущий HTTP-запрос с формой.
        collection_id: Идентификатор коллекции из пути.
        use_case: Сценарий удаления элемента коллекции.

    Returns:
        Response: 401 для гостя.
        RedirectResponse: Редирект на страницу коллекций.
    """
    user = await get_current_user(request)
    if not user:
        return Response(status_code=HTTPStatus.UNAUTHORIZED)
    body = await read_form_model(request, RemoveCollectionItemRequest)
    if body is None:
        await flash(request, "Не указано аниме для удаления")
        return redirect_collections(request)
    try:
        await use_case.execute(
            RemoveCollectionItemCommand(
                collection_id=collection_id,
                anime_id=body.anime_id,
                user_id=user.id,
            )
        )
    except CollectionAccessError as error:
        await flash(request, str(error))
    return redirect_collections(request)


@collection_router.get(
    "/api/mine",
    name="collection.my_collections_api",
    response_model=MyCollectionsResponse,
    responses={HTTPStatus.UNAUTHORIZED: {"model": ErrorResponse}},
)
async def my_collections_api(
    request: Request,
    use_case: FromDishka[GetUserCollectionsUseCase],
):
    """Отдать коллекции пользователя в JSON для выбора в интерфейсе.

    Args:
        request: Текущий HTTP-запрос.
        use_case: Сценарий списка коллекций.

    Returns:
        MyCollectionsResponse: Краткие карточки коллекций пользователя сессии.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    details = await use_case.execute(GetUserCollectionsQuery(user_id=user.id))
    return MyCollectionsResponse(
        collections=[
            CollectionSummaryResponse(id=item.collection.id, title=item.collection.title)
            for item in details
        ]
    )


@collection_router.get("/share/{collection_id}", name="collection.shared_collection_page")
async def shared_collection_page(
    request: Request,
    collection_id: int,
    use_case: FromDishka[GetSharedCollectionUseCase],
):
    """Отдать страницу коллекции по ссылке.

    Args:
        request: Текущий HTTP-запрос.
        collection_id: Идентификатор публичной коллекции.
        use_case: Сценарий чтения общей коллекции.

    Returns:
        HTMLResponse: Отрисованный шаблон публичной коллекции.
    """
    details = await use_case.execute(GetSharedCollectionQuery(collection_id=collection_id))
    return await render_template(request, "collection/share.html", collection=details)


def redirect_login(request: Request) -> RedirectResponse:
    """Собрать перенаправление на страницу входа.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        RedirectResponse: 303 на страницу входа.
    """
    return RedirectResponse(
        url=request.app.url_path_for("auth.login_page"),
        status_code=HTTPStatus.SEE_OTHER,
    )


def redirect_collections(request: Request) -> RedirectResponse:
    """Собрать перенаправление на страницу коллекций.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        RedirectResponse: 303 на страницу коллекций.
    """
    return RedirectResponse(
        url=request.app.url_path_for("collection.collections_page"),
        status_code=HTTPStatus.SEE_OTHER,
    )
