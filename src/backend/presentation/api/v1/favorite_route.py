"""Favorite routes: add, remove, list favorites with recommendations."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Request
from fastapi.responses import Response

from backend.infrastructure.web import render_template
from backend.presentation.api.helpers import get_container, read_payload

favorite_router = APIRouter(prefix="/favorites")
favorite_bp = favorite_router
container = None


def _extract_favorite_payload(payload, user_id_fallback=None):
    """Extract favorite fields from a payload dict.

    Args:
        payload: Raw payload dictionary.
        user_id_fallback: Fallback user ID if not in payload.

    Returns:
        dict: Normalized favorite payload.
    """
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
    """Add an anime to user favorites.

    Args:
        request: Current HTTP request with favorite data.

    Returns:
        Response: 201 Created on success, 400 on invalid payload.
    """
    container = get_container(request)
    payload = _extract_favorite_payload(await read_payload(request))
    if payload["user_id"] is None or payload["anime_id"] is None:
        return Response(status_code=HTTPStatus.BAD_REQUEST)
    await container.add_favorite_use_case().execute(**payload)
    return Response(status_code=HTTPStatus.CREATED)


@favorite_router.delete("/", name="favorite.remove_favorite")
async def remove_favorite(request: Request):
    """Remove an anime from user favorites.

    Args:
        request: Current HTTP request with favorite data.

    Returns:
        Response: 204 No Content on success, 400 on invalid payload.
    """
    container = get_container(request)
    payload = _extract_favorite_payload(await read_payload(request))
    if payload["user_id"] is None or payload["anime_id"] is None:
        return Response(status_code=HTTPStatus.BAD_REQUEST)
    await container.remove_favorite_use_case().execute(
        user_id=payload["user_id"],
        anime_id=payload["anime_id"],
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@favorite_router.get("/{user_id}", name="favorite.get_favorites")
async def get_favorites(request: Request, user_id: int):
    """Render the user's favorites page with recommendations.

    Args:
        request: Current HTTP request.
        user_id: User ID from path.

    Returns:
        HTMLResponse: Rendered favorites list template.
    """
    container = get_container(request)
    favorites = await container.get_favorites_use_case().execute(user_id=user_id)
    recommendations = await container.generate_recommendations_use_case().execute(user_id=user_id)
    return render_template(
        request,
        "favorite/list.html",
        favorites=favorites,
        recommendations=recommendations,
        user_id=user_id,
    )
