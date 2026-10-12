"""Password reset request and confirmation routes."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.use_cases.auth.password_reset.request_password_reset import (
    RequestPasswordResetUseCase,
)
from backend.application.use_cases.auth.password_reset.reset_password import (
    ResetPasswordUseCase,
)
from backend.infrastructure.security import client_ip
from backend.infrastructure.web import render_template
from backend.presentation.api.auth_responses import (
    redirect,
    redirect_confirm,
    resolve,
)
from backend.presentation.api.requests.auth_mapper import (
    FormValidationError,
    map_confirm_password_reset_command,
    map_request_password_reset_command,
)
from backend.utils import log_security_event

password_reset_router = APIRouter(route_class=DishkaRoute)


@password_reset_router.get("/password-reset", name="auth.password_reset_request_page")
async def password_reset_request_page(request: Request):
    """Render the password reset request page.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered password reset request page.
    """
    return await render_template(request, "auth/password_reset_request.html")


@password_reset_router.get(
    "/password-reset/confirm",
    name="auth.password_reset_confirm_page",
)
async def password_reset_confirm_page(request: Request):
    """Render the password reset confirmation page.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered confirmation page.
    """
    token = str(request.query_params.get("token", ""))
    return await render_template(request, "auth/password_reset_confirm.html", token=token)


@password_reset_router.post("/password-reset", name="auth.request_password_reset")
async def request_password_reset(
    request: Request,
    use_case: FromDishka[RequestPasswordResetUseCase],
):
    """Request a password reset email for a user.

    Args:
        request: Incoming HTTP request.
        use_case: Request password reset use case.

    Returns:
        RedirectResponse: Redirect back to the password reset request page.
    """
    form = await request.form()
    try:
        command = await map_request_password_reset_command(
            form, base_url=str(request.base_url).rstrip("/")
        )
    except FormValidationError:
        return await redirect(request, "auth.password_reset_request_page")
    await log_security_event(
        event="password_reset_requested",
        email=command.email,
        ip_address=await client_ip(request),
    )
    await use_case.execute(email=command.email, base_url=command.base_url)
    return await redirect(request, "auth.password_reset_request_page")


@password_reset_router.post("/password-reset/confirm", name="auth.confirm_password_reset")
async def confirm_password_reset(request: Request, use_case: FromDishka[ResetPasswordUseCase]):
    """Confirm a password reset with a token and new password.

    Args:
        request: Incoming HTTP request.
        use_case: Reset password use case.

    Returns:
        RedirectResponse: Redirect to login on success.
    """
    form = await request.form()
    try:
        command = await map_confirm_password_reset_command(form)
    except FormValidationError as error:
        return await redirect_confirm(request, str(error))
    await log_security_event(event="password_reset_success", ip_address=await client_ip(request))
    result = await use_case.execute(token=command.token, new_password=command.password)
    return await resolve(request, result)
