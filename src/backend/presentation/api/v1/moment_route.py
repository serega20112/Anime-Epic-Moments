"""Thin HTTP routes for viewing moments (draft auto-highlights)."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.application.dto import (
    PublishViewingMomentCommand,
    SaveViewingMomentCommand,
)
from backend.application.use_cases import (
    DeleteViewingMomentUseCase,
    GetUserViewingMomentsUseCase,
    PublishViewingMomentUseCase,
    SaveViewingMomentUseCase,
)
from backend.presentation.api.helpers import get_current_user, read_payload

watch_moment_router = APIRouter(prefix="/watch", route_class=DishkaRoute)
moment_router = APIRouter(prefix="/moments", route_class=DishkaRoute)


async def _moment_payload(moment) -> dict:
    """Serialize a viewing moment for JSON responses.

    Args:
        moment: Viewing moment domain object.

    Returns:
        dict: Serialized moment.
    """
    return {
        "id": moment.id,
        "anime_id": moment.anime_id,
        "episode": moment.episode,
        "timestamp": moment.timestamp,
        "watch_source_id": moment.watch_source_id,
        "caption": moment.caption,
        "sticker": moment.sticker,
        "screenshot_url": moment.screenshot_url,
        "created_at": moment.created_at.isoformat() if moment.created_at else None,
    }


async def _optional_str(value: str | None) -> str | None:
    """Trim a string or return None for blank values.

    Args:
        value: Raw value.

    Returns:
        str | None: Trimmed value or None.
    """
    if value is None:
        return None
    return str(value).strip() or None


async def _to_float(value, default: float = 0.0) -> float:
    """Convert a value to a float with a fallback.

    Args:
        value: Raw value.
        default: Fallback value.

    Returns:
        float: Parsed float.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


async def _to_int(value) -> int | None:
    """Convert a value to an int or return None.

    Args:
        value: Raw value.

    Returns:
        int | None: Parsed integer or None.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@watch_moment_router.post("/{anime_id}/moments", name="watch.save_moment")
async def save_moment(
    request: Request,
    anime_id: int,
    use_case: FromDishka[SaveViewingMomentUseCase],
):
    """Create or update a draft viewing moment from the player.

    Args:
        request: Incoming HTTP request with JSON payload.
        anime_id: Anime ID from path.
        use_case: Save viewing moment use case.

    Returns:
        JSONResponse: Created moment or an error.
    """
    user = await get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    payload = await read_payload(request)
    command = SaveViewingMomentCommand(
        user_id=user.id,
        anime_id=anime_id,
        episode=await _to_int(payload.get("episode")) or 1,
        timestamp=await _to_float(payload.get("timestamp")),
        watch_source_id=await _to_int(payload.get("watch_source_id")),
        caption=await _optional_str(payload.get("caption")),
        sticker=await _optional_str(payload.get("sticker")),
        screenshot_url=await _optional_str(payload.get("screenshot_url")),
        moment_id=await _to_int(payload.get("moment_id")),
    )
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return JSONResponse(await _moment_payload(result.data), status_code=result.status_code)


@moment_router.get("", name="moment.get_user_moments")
async def get_user_moments(
    request: Request,
    use_case: FromDishka[GetUserViewingMomentsUseCase],
):
    """Return the current user's draft viewing moments.

    Args:
        request: Incoming HTTP request.
        use_case: Get user viewing moments use case.

    Returns:
        JSONResponse: List of moments or an error.
    """
    user = await get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    result = await use_case.execute(user.id)
    return [await _moment_payload(item) for item in result.data]


@moment_router.post("/{moment_id}/publish", name="moment.publish_moment")
async def publish_moment(
    request: Request,
    moment_id: int,
    use_case: FromDishka[PublishViewingMomentUseCase],
):
    """Publish a draft moment as a highlight.

    Args:
        request: Incoming HTTP request with optional overrides.
        moment_id: Moment ID from path.
        use_case: Publish viewing moment use case.

    Returns:
        JSONResponse: Created highlight or an error.
    """
    user = await get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    payload = await read_payload(request)
    command = PublishViewingMomentCommand(
        user_id=user.id,
        moment_id=moment_id,
        is_spoiler=bool(payload.get("is_spoiler")),
        title=await _optional_str(payload.get("title")),
        category=await _optional_str(payload.get("category")),
        emotion=await _optional_str(payload.get("emotion")),
        description=await _optional_str(payload.get("description")),
    )
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return JSONResponse({"highlight_id": result.data.id}, status_code=result.status_code)


@moment_router.delete("/{moment_id}", name="moment.delete_moment")
async def delete_moment(
    request: Request,
    moment_id: int,
    use_case: FromDishka[DeleteViewingMomentUseCase],
):
    """Delete a draft viewing moment.

    Args:
        request: Incoming HTTP request.
        moment_id: Moment ID from path.
        use_case: Delete viewing moment use case.

    Returns:
        JSONResponse: Deletion result or an error.
    """
    user = await get_current_user(request)
    if not user:
        return JSONResponse({"error": "auth_required"}, status_code=401)
    result = await use_case.execute(moment_id, user.id)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return result.data
