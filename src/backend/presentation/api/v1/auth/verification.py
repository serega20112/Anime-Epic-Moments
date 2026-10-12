"""Email verification routes."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.use_cases.auth.verification.resend_email_verification import (
    ResendEmailVerificationUseCase,
)
from backend.application.use_cases.auth.verification.verify_email import VerifyEmailUseCase
from backend.infrastructure.security import client_ip
from backend.infrastructure.web import render_template
from backend.presentation.api.auth_responses import (
    redirect_verify,
    resolve_auth,
    resolve_verify,
)
from backend.presentation.api.requests.auth_mapper import (
    FormValidationError,
    map_resend_verification_command,
    map_verify_email_command,
)
from backend.utils import log_security_event

verification_router = APIRouter(route_class=DishkaRoute)


@verification_router.get("/verify-email", name="auth.verify_email_page")
async def verify_email_page(request: Request):
    """Render the email verification page.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered verification page.
    """
    return await render_template(
        request,
        "auth/verify_email.html",
        email=str(request.query_params.get("email") or "").strip(),
    )


@verification_router.post("/verify-email", name="auth.verify_email")
async def verify_email(request: Request, use_case: FromDishka[VerifyEmailUseCase]):
    """Verify an email verification code and complete registration.

    Args:
        request: Incoming HTTP request.
        use_case: Verify email use case.

    Returns:
        RedirectResponse: Redirect to the index page on success.
    """
    form = await request.form()
    try:
        command = await map_verify_email_command(form)
    except FormValidationError as error:
        return await redirect_verify(request, str(error))
    result = await use_case.execute(email=command.email, code=command.code)
    return await resolve_auth(request, result)


@verification_router.post("/verify-email/resend", name="auth.resend_verification_email")
async def resend_verification_email(
    request: Request,
    use_case: FromDishka[ResendEmailVerificationUseCase],
):
    """Resend the email verification code.

    Args:
        request: Incoming HTTP request.
        use_case: Resend email verification use case.

    Returns:
        RedirectResponse: Redirect back to the verification page.
    """
    form = await request.form()
    try:
        command = await map_resend_verification_command(form)
    except FormValidationError as error:
        return await redirect_verify(request, str(error))
    await log_security_event(
        event="email_verification_resend_requested",
        email=command.email,
        ip_address=await client_ip(request),
    )
    result = await use_case.execute(email=command.email)
    return await resolve_verify(request, result)
