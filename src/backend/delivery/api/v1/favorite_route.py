from fastapi import APIRouter, Request
from fastapi.responses import Response

from src.backend.delivery.api.helpers import get_container, read_payload
from src.backend.infrastructure.web.templating import render_template

favorite_router = APIRouter(prefix="/favorites")
favorite_bp = favorite_router
container = None


def _extract_favorite_payload(payload, user_id_fallback=None):
    return {
        "user_id": payload.get("user_id", user_id_fallback),
        "anime_id": payload.get("anime_id"),
        "title": payload.get("title"),
        "description": payload.get("description"),
        "cover_url": payload.get("cover_url"),
        "genres": payload.get("genres"),
    }


@favorite_router.post("/", name="favorite.add_favorite")
async def add_favorite(request: Request):
    container = get_container(request)
    payload = _extract_favorite_payload(await read_payload(request))
    if payload["user_id"] is None or payload["anime_id"] is None:
        return Response(status_code=400)
    await container.add_favorite_use_case().execute(**payload)
    return Response(status_code=201)


@favorite_router.delete("/", name="favorite.remove_favorite")
async def remove_favorite(request: Request):
    container = get_container(request)
    payload = _extract_favorite_payload(await read_payload(request))
    if payload["user_id"] is None or payload["anime_id"] is None:
        return Response(status_code=400)
    await container.remove_favorite_use_case().execute(
        user_id=payload["user_id"],
        anime_id=payload["anime_id"],
    )
    return Response(status_code=204)


@favorite_router.get("/{user_id}", name="favorite.get_favorites")
async def get_favorites(request: Request, user_id: int):
    container = get_container(request)
    favorites = await container.get_favorites_use_case().execute(user_id=user_id)
    recommendations = await container.generate_recommendations_use_case().execute(
        user_id=user_id
    )
    return render_template(
        request,
        "favorite/list.html",
        favorites=favorites,
        recommendations=recommendations,
        user_id=user_id,
    )
