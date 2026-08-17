"""Support routes: render support page and create support tickets."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from backend.application.use_cases import CreateSupportTicketUseCase
from backend.config import Settings
from backend.infrastructure.security.flask_protection import client_ip, rate_limit
from backend.infrastructure.security.rate_limit_keys import support_ticket_subject
from backend.infrastructure.web import flash, render_template
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.support_form_builder import (
    build_default_support_form,
    build_support_form_data,
)
from backend.presentation.api.requests.support_mapper import map_create_support_ticket_command
from backend.utils import log_business_event

support_router = APIRouter(prefix="/support", route_class=DishkaRoute)
support_bp = support_router


async def _support_ticket_subject(request: Request) -> str:
    """Build a composite rate-limit subject for support ticket creation."""
    return await support_ticket_subject(
        ip_address=await client_ip(request),
        user_id=getattr(await get_current_user(request), "id", None),
    )


@support_router.get("", name="support.support_page")
async def support_page(request: Request):
    """Render the support ticket creation page.

    Args:
        request: Current HTTP request.

    Returns:
        HTMLResponse: Rendered support page template.
    """
    return await _render_support_page(request)


@support_router.post("", name="support.create_support_ticket")
@rate_limit(
    scope="support_ticket_create",
    limit=Settings.support_ticket_rate_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=_support_ticket_subject,
    response_mode="redirect",
    redirect_endpoint="support.support_page",
)
async def create_support_ticket(
    request: Request,
    use_case: FromDishka[CreateSupportTicketUseCase],
):
    """Create a support ticket from form data.

    Args:
        request: Current HTTP request with form data.
        use_case: Create support ticket use case.

    Returns:
        RedirectResponse: Redirect to support page after creation.
    """
    user = await get_current_user(request)
    user_id = getattr(user, "id", None)
    command = await map_create_support_ticket_command(
        dict(await request.form()),
        user_id=user_id,
        user_email=getattr(user, "email", None),
        user_username=getattr(user, "username", None),
    )

    result = await use_case.execute(command)

    if not result.ok:
        await flash(request, result.error_message or "Не удалось создать тикет поддержки")
        return await _render_support_page(
            request,
            form_data=await build_support_form_data(
                command=command,
                user_email=getattr(user, "email", None),
                user_username=getattr(user, "username", None),
            ),
            status_code=result.status_code,
        )

    ticket = result.data
    await log_business_event(
        event="support_ticket_created",
        user_id=ticket.user_id,
        ip_address=await client_ip(request),
        details={
            "ticket_id": getattr(ticket, "id", None),
            "delivery_status": ticket.delivery_status,
        },
    )
    await flash(request, result.message or "Тикет отправлен в поддержку.")
    return RedirectResponse(
        url=request.app.url_path_for("support.support_page"),
        status_code=HTTPStatus.SEE_OTHER,
    )


async def _render_support_page(
    request: Request,
    form_data: dict[str, str] | None = None,
    status_code: int = HTTPStatus.OK,
):
    """Render the support page with optional form data.

    Args:
        request: Current HTTP request.
        form_data: Pre-filled form data for re-display.
        status_code: HTTP status code for the response.

    Returns:
        HTMLResponse: Rendered support page template.
    """
    return await render_template(
        request,
        "support/create.html",
        support_form=form_data or await _default_form(request),
        status_code=status_code,
    )


async def _default_form(request: Request) -> dict[str, str]:
    """Build default form data for the GET support page.

    Args:
        request: Current HTTP request.

    Returns:
        dict[str, str]: Normalized default form data.
    """
    user = await get_current_user(request)
    return await build_default_support_form(
        user_email=getattr(user, "email", ""),
        user_username=getattr(user, "username", ""),
        channel_param=request.query_params.get("channel"),
        page_param=request.query_params.get("page"),
    )
