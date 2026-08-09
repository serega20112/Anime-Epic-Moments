"""Support routes: render support page and create support tickets."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from backend.infrastructure.security.rate_limit_keys import support_ticket_subject
from backend.presentation.api.requests.support_mapper import map_create_support_ticket_command

from backend.config import Settings
from backend.infrastructure.security.flask_protection import client_ip, rate_limit
from backend.infrastructure.web import flash, render_template
from backend.presentation.api.helpers import get_container, get_current_user
from backend.presentation.api.requests.support_form_builder import (
    build_default_support_form,
    build_support_form_data,
)
from backend.utils import log_business_event

support_router = APIRouter(prefix="/support")
support_bp = support_router


@support_router.get("", name="support.support_page")
async def support_page(request: Request):
    """Render the support ticket creation page.

    Args:
        request: Current HTTP request.

    Returns:
        HTMLResponse: Rendered support page template.
    """
    return _render_support_page(request)


@support_router.post("", name="support.create_support_ticket")
@rate_limit(
    scope="support_ticket_create",
    limit=Settings.support_ticket_rate_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=lambda request: support_ticket_subject(
        ip_address=client_ip(request),
        user_id=getattr(get_current_user(request), "id", None),
    ),
    response_mode="redirect",
    redirect_endpoint="support.support_page",
)
async def create_support_ticket(request: Request):
    """Create a support ticket from form data.

    Args:
        request: Current HTTP request with form data.

    Returns:
        RedirectResponse: Redirect to support page after creation.
    """
    container = get_container(request)
    user = get_current_user(request)
    user_id = getattr(user, "id", None)
    command = map_create_support_ticket_command(
        dict(await request.form()),
        user_id=user_id,
        user_email=getattr(user, "email", None),
        user_username=getattr(user, "username", None),
    )

    result = await container.create_support_ticket_use_case().execute(command)

    if not result.ok:
        flash(request, result.error_message or "Не удалось создать тикет поддержки")
        return _render_support_page(
            request,
            form_data=build_support_form_data(
                command=command,
                user_email=getattr(user, "email", None),
                user_username=getattr(user, "username", None),
            ),
            status_code=result.status_code,
        )

    ticket = result.data
    log_business_event(
        event="support_ticket_created",
        user_id=ticket.user_id,
        ip_address=client_ip(request),
        details={
            "ticket_id": getattr(ticket, "id", None),
            "delivery_status": ticket.delivery_status,
        },
    )
    flash(request, result.message or "Тикет отправлен в поддержку.")
    return RedirectResponse(
        url=request.app.url_path_for("support.support_page"),
        status_code=HTTPStatus.SEE_OTHER,
    )


def _render_support_page(
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
    return render_template(
        request,
        "support/create.html",
        support_form=form_data or _default_form(request),
        status_code=status_code,
    )


def _default_form(request: Request) -> dict[str, str]:
    """Build default form data for the GET support page.

    Args:
        request: Current HTTP request.

    Returns:
        dict[str, str]: Normalized default form data.
    """
    user = get_current_user(request)
    return build_default_support_form(
        user_email=getattr(user, "email", ""),
        user_username=getattr(user, "username", ""),
        channel_param=request.query_params.get("channel"),
        page_param=request.query_params.get("page"),
    )
