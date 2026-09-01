"""Thin HTTP routes for anime collection management."""

from __future__ import annotations

from dataclasses import replace
from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

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
from backend.infrastructure.files.uploads import UploadValidationError, save_image
from backend.infrastructure.web import flash, render_template
from backend.presentation.api.helpers import get_current_user, read_payload, wants_json
from backend.presentation.api.requests.collection_mapper import (
    map_add_collection_item_command,
    map_create_collection_command,
    map_remove_collection_item_command,
)

collection_router = APIRouter(prefix="/collections", route_class=DishkaRoute)
collection_bp = collection_router


@collection_router.get("", name="collection.collections_page")
async def collections_page(
    request: Request,
    collections_use_case: FromDishka[GetUserCollectionsUseCase],
    favorites_use_case: FromDishka[GetFavoritesUseCase],
):
    """Render the user's collections and favorites page.

    Args:
        request: Incoming HTTP request.
        collections_use_case: Get user collections use case.
        favorites_use_case: Get favorites use case.

    Returns:
        RedirectResponse: Login redirect for guests.
        HTMLResponse: Rendered collections list template.
    """
    user = await get_current_user(request)
    if not user:
        return await redirect_login(request)
    collections = await collections_use_case.execute(user.id)
    favorites = await favorites_use_case.execute(user.id)
    return await render_template(
        request,
        "collection/list.html",
        collections=collections,
        favorites=favorites,
    )


@collection_router.post("", name="collection.create_collection")
async def create_collection(request: Request, use_case: FromDishka[CreateCollectionUseCase]):
    """Create a new collection from form data.

    The cover is taken from an uploaded file when present, otherwise from the
    ``cover_url`` field. Uploaded files are stored under ``/static/uploads``.

    Args:
        request: Incoming HTTP request with form data.
        use_case: Create collection use case.

    Returns:
        Response: 401 for guests.
        RedirectResponse: Redirect to the collections page.
    """
    user = await get_current_user(request)
    if not user:
        return Response(status_code=HTTPStatus.UNAUTHORIZED)
    form = await request.form()
    cover_url = str(form.get("cover_url") or "").strip() or None
    cover_file = form.get("cover_file")
    if cover_file is not None and getattr(cover_file, "filename", None):
        try:
            cover_url = await save_image(cover_file, "covers")
        except UploadValidationError as error:
            await flash(request, str(error))
            return await redirect_collections(request)
    command = await map_create_collection_command(form, user_id=user.id)
    command = replace(command, cover_url=cover_url)
    try:
        await use_case.execute(command)
    except ValueError as error:
        await flash(request, str(error))
        return await redirect_collections(request)
    return await redirect_collections(request)


@collection_router.post("/{collection_id}/items", name="collection.add_collection_item")
async def add_collection_item(
    request: Request,
    collection_id: int,
    use_case: FromDishka[AddCollectionItemUseCase],
):
    """Add an anime item to a collection.

    Accepts both JSON payloads (picker UI) and classic form posts. Snapshot
    fields are optional: when only the anime id is sent the use case resolves
    the snapshot server-side. Only the collection owner may add items.

    Args:
        request: Incoming HTTP request with JSON or form data.
        collection_id: Collection ID from path.
        use_case: Add collection item use case.

    Returns:
        Response: 401 for guests.
        JSONResponse: 201 on success, 403/400 on access or validation errors.
        RedirectResponse: Redirect to the collections page for form posts.
    """
    user = await get_current_user(request)
    if not user:
        return Response(status_code=HTTPStatus.UNAUTHORIZED)
    command = await map_add_collection_item_command(
        await read_payload(request),
        collection_id=collection_id,
        user_id=user.id,
    )
    try:
        await use_case.execute(command)
    except CollectionAccessError as error:
        if await wants_json(request):
            return JSONResponse({"error": str(error)}, status_code=HTTPStatus.FORBIDDEN)
        await flash(request, str(error))
        return await redirect_collections(request)
    except ValueError as error:
        if await wants_json(request):
            return JSONResponse({"error": str(error)}, status_code=HTTPStatus.BAD_REQUEST)
        await flash(request, str(error))
        return await redirect_collections(request)
    if await wants_json(request):
        return JSONResponse({"status": "added"}, status_code=HTTPStatus.CREATED)
    return await redirect_collections(request)


@collection_router.post(
    "/{collection_id}/items/remove",
    name="collection.remove_collection_item",
)
async def remove_collection_item(
    request: Request,
    collection_id: int,
    use_case: FromDishka[RemoveCollectionItemUseCase],
):
    """Remove an anime item from a collection.

    Args:
        request: Incoming HTTP request with form data.
        collection_id: Collection ID from path.
        use_case: Remove collection item use case.

    Returns:
        Response: 401 for guests.
        RedirectResponse: Redirect to the collections page.
    """
    user = await get_current_user(request)
    if not user:
        return Response(status_code=HTTPStatus.UNAUTHORIZED)
    command = await map_remove_collection_item_command(
        await request.form(), collection_id=collection_id
    )
    await use_case.execute(command)
    return await redirect_collections(request)


@collection_router.get("/api/mine", name="collection.my_collections_api")
async def my_collections_api(
    request: Request,
    use_case: FromDishka[GetUserCollectionsUseCase],
):
    """Return the current user's collections as JSON for the picker UI.

    Args:
        request: Incoming HTTP request.
        use_case: Get user collections use case.

    Returns:
        Response: 401 for guests.
        JSONResponse: Collection id/title pairs.
    """
    user = await get_current_user(request)
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=HTTPStatus.UNAUTHORIZED)
    details = await use_case.execute(user.id)
    return JSONResponse(
        {
            "collections": [
                {"id": item.collection.id, "title": item.collection.title} for item in details
            ]
        }
    )


@collection_router.get("/share/{collection_id}", name="collection.shared_collection_page")
async def shared_collection_page(
    request: Request,
    collection_id: int,
    use_case: FromDishka[GetSharedCollectionUseCase],
):
    """Render a shared collection page.

    Args:
        request: Incoming HTTP request.
        collection_id: Collection ID from path.
        use_case: Get shared collection use case.

    Returns:
        HTMLResponse: Rendered shared collection template.
    """
    details = await use_case.execute(collection_id)
    return await render_template(request, "collection/share.html", collection=details)


async def redirect_login(request: Request) -> RedirectResponse:
    """Build a redirect to the login page.

    Args:
        request: Incoming HTTP request.

    Returns:
        RedirectResponse: SEE_OTHER redirect to login.
    """
    return RedirectResponse(
        url=request.app.url_path_for("auth.login_page"),
        status_code=HTTPStatus.SEE_OTHER,
    )


async def redirect_collections(request: Request) -> RedirectResponse:
    """Build a redirect to the collections page.

    Args:
        request: Incoming HTTP request.

    Returns:
        RedirectResponse: SEE_OTHER redirect to the collections page.
    """
    return RedirectResponse(
        url=request.app.url_path_for("collection.collections_page"),
        status_code=HTTPStatus.SEE_OTHER,
    )
