"""Highlight create, edit and delete routes."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from backend.application.use_cases import DeleteHighlightUseCase, EditHighlightUseCase
from backend.application.use_cases.highlight.crud.create_highlight import CreateHighlightUseCase
from backend.infrastructure.security.flask_protection import client_ip, rate_limit
from backend.presentation.api.helpers import get_current_user, read_payload
from backend.presentation.api.requests.highlight_mapper import (
    map_create_highlight_command,
    map_delete_highlight_command,
    map_edit_highlight_command,
)

highlight_items_router = APIRouter(route_class=DishkaRoute)


async def _create_highlight_subject(request: Request) -> str:
    """Build a composite rate-limit subject for highlight creation."""
    ip = await client_ip(request)
    user_id = getattr(await get_current_user(request), "id", "guest")
    return f"{ip}::{user_id}"


@highlight_items_router.post("/", name="highlight.create_highlight")
@rate_limit(
    scope="highlight_create",
    limit=20,
    window_seconds=60,
    key_builder=_create_highlight_subject,
)
async def create_highlight(
    request: Request,
    use_case: FromDishka[CreateHighlightUseCase],
):
    """Create a new highlight from JSON payload.

    Args:
        request: Incoming HTTP request with highlight data.
        use_case: Create highlight use case.

    Returns:
        JSONResponse: Created highlight ID with 201 status or an error.
    """
    payload = await read_payload(request)
    user = await get_current_user(request)
    command = await map_create_highlight_command(payload, user_id=user.id if user else None)
    if command is None:
        return JSONResponse(
            {"error": "invalid_payload"},
            status_code=HTTPStatus.BAD_REQUEST,
        )
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return JSONResponse(
        {"highlight_id": getattr(result.data, "id", None)},
        status_code=result.status_code,
    )


@highlight_items_router.put("/{highlight_id}", name="highlight.edit_highlight")
async def edit_highlight(
    request: Request,
    highlight_id: int,
    use_case: FromDishka[EditHighlightUseCase],
):
    """Edit an existing highlight.

    Args:
        request: Incoming HTTP request with updated data.
        highlight_id: Highlight ID from path.
        use_case: Edit highlight use case.

    Returns:
        JSONResponse: 204 on success or an error.
    """
    payload = await read_payload(request)
    command = await map_edit_highlight_command(payload, highlight_id=highlight_id)
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return Response(status_code=result.status_code)


@highlight_items_router.delete("/{highlight_id}", name="highlight.delete_highlight")
async def delete_highlight(
    request: Request,
    highlight_id: int,
    use_case: FromDishka[DeleteHighlightUseCase],
):
    """Delete a highlight.

    Args:
        request: Incoming HTTP request.
        highlight_id: Highlight ID from path.
        use_case: Delete highlight use case.

    Returns:
        JSONResponse: 204 on success or an error.
    """
    command = await map_delete_highlight_command(highlight_id=highlight_id)
    result = await use_case.execute(command)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=result.status_code)
    return Response(status_code=result.status_code)
