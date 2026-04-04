from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, Response

from src.backend.delivery.api.helpers import get_container, get_current_user
from src.backend.infrastructure.web.templating import render_template

collection_router = APIRouter(prefix="/collections")
collection_bp = collection_router
container = None


@collection_router.get("", name="collection.collections_page")
async def collections_page(request: Request):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return RedirectResponse(
            url=request.app.url_path_for("auth.login_page"),
            status_code=303,
        )
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
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return Response(status_code=401)
    form = await request.form()
    await container.create_collection_use_case().execute(
        user_id=user.id,
        title=str(form.get("title") or "").strip(),
        description=str(form.get("description") or "").strip(),
        is_public=str(form.get("is_public") or "1").strip() in {"1", "true", "on"},
    )
    return RedirectResponse(
        url=request.app.url_path_for("collection.collections_page"),
        status_code=303,
    )


@collection_router.post("/{collection_id}/items", name="collection.add_collection_item")
async def add_collection_item(request: Request, collection_id: int):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return Response(status_code=401)
    form = await request.form()
    genres = form.getlist("genres")
    if len(genres) == 1 and genres[0]:
        genres = [item.strip() for item in str(genres[0]).split(",") if item.strip()]
    await container.add_collection_item_use_case().execute(
        collection_id=collection_id,
        anime_id=int(form.get("anime_id") or 0),
        title=str(form.get("title") or "").strip(),
        description=str(form.get("description") or "").strip(),
        cover_url=str(form.get("cover_url") or "").strip() or None,
        genres=genres,
    )
    return RedirectResponse(
        url=request.app.url_path_for("collection.collections_page"),
        status_code=303,
    )


@collection_router.post(
    "/{collection_id}/items/remove",
    name="collection.remove_collection_item",
)
async def remove_collection_item(request: Request, collection_id: int):
    container = get_container(request)
    user = get_current_user(request)
    if not user:
        return Response(status_code=401)
    form = await request.form()
    await container.remove_collection_item_use_case().execute(
        collection_id=collection_id,
        anime_id=int(form.get("anime_id") or 0),
    )
    return RedirectResponse(
        url=request.app.url_path_for("collection.collections_page"),
        status_code=303,
    )


@collection_router.get("/share/{collection_id}", name="collection.shared_collection_page")
async def shared_collection_page(request: Request, collection_id: int):
    container = get_container(request)
    details = await container.get_shared_collection_use_case().execute(collection_id)
    return render_template(request, "collection/share.html", collection=details)
