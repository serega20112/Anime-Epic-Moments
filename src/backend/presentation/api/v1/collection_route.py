"""Thin HTTP routes for anime collection management."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, Response
from backend.presentation.api.requests.collection_mapper import (
    map_add_collection_item_command,
    map_create_collection_command,
    map_remove_collection_item_command,
)

from backend.infrastructure.web import render_template
from backend.presentation.api.helpers import get_container, get_current_user

collection_router = APIRouter(prefix="/collections")
collection_bp = collection_router


@collection_router.get("", name="collection.collections_page")
async def collections_page(request: Request):
    """Render the user's collections and favorites page.

    Args:
        request: Incoming HTTP request.

    Returns:
        RedirectResponse: Login redirect for guests.
        HTMLResponse: Rendered collections list template.
    """
    user = get_current_user(request)
    if not user:
        return redirect_login(request)
    container = get_container(request)
    collections = await container.get_user_collections_use_case().execute(user.id)
    favorites = await container.get_favorites_use_case().execute(user.id)
    return render_template(
        request,
        "collection/list.html",
        collections=collections,
        favorites=favorites,
    )


@collection_router.post("", name="collection.create_collection")
async def create_collection(request: Request):
    """Create a new collection from form data.

    Args:
        request: Incoming HTTP request with form data.

    Returns:
        Response: 401 for guests.
        RedirectResponse: Redirect to the collections page.
    """
    user = get_current_user(request)
    if not user:
        return Response(status_code=HTTPStatus.UNAUTHORIZED)
    container = get_container(request)
    command = map_create_collection_command(await request.form(), user_id=user.id)
    await container.create_collection_use_case().execute(command)
    return redirect_collections(request)


@collection_router.post("/{collection_id}/items", name="collection.add_collection_item")
async def add_collection_item(request: Request, collection_id: int):
    """Add an anime item to a collection.

    Args:
        request: Incoming HTTP request with form data.
        collection_id: Collection ID from path.

    Returns:
        Response: 401 for guests.
        RedirectResponse: Redirect to the collections page.
    """
    user = get_current_user(request)
    if not user:
        return Response(status_code=HTTPStatus.UNAUTHORIZED)
    container = get_container(request)
    command = map_add_collection_item_command(
        await request.form(), collection_id=collection_id
    )
    await container.add_collection_item_use_case().execute(command)
    return redirect_collections(request)


@collection_router.post(
    "/{collection_id}/items/remove",
    name="collection.remove_collection_item",
)
async def remove_collection_item(request: Request, collection_id: int):
    """Remove an anime item from a collection.

    Args:
        request: Incoming HTTP request with form data.
        collection_id: Collection ID from path.

    Returns:
        Response: 401 for guests.
        RedirectResponse: Redirect to the collections page.
    """
    user = get_current_user(request)
    if not user:
        return Response(status_code=HTTPStatus.UNAUTHORIZED)
    container = get_container(request)
    command = map_remove_collection_item_command(
        await request.form(), collection_id=collection_id
    )
    await container.remove_collection_item_use_case().execute(command)
    return redirect_collections(request)


@collection_router.get("/share/{collection_id}", name="collection.shared_collection_page")
async def shared_collection_page(request: Request, collection_id: int):
    """Render a shared collection page.

    Args:
        request: Incoming HTTP request.
        collection_id: Collection ID from path.

    Returns:
        HTMLResponse: Rendered shared collection template.
    """
    container = get_container(request)
    details = await container.get_shared_collection_use_case().execute(collection_id)
    return render_template(request, "collection/share.html", collection=details)


def redirect_login(request: Request) -> RedirectResponse:
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


def redirect_collections(request: Request) -> RedirectResponse:
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
