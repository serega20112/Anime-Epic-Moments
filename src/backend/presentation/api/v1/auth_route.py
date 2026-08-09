"""Thin HTTP routes for authentication, sessions and profile management."""

from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from backend.presentation.api.auth_responses import (
    clear_auth_cookies,
    get_container,
    redirect,
    redirect_confirm,
    redirect_verify,
    resolve,
    resolve_auth,
    resolve_verify,
    set_auth_cookies,
)
from backend.presentation.api.requests.auth_mapper import (
    FormValidationError,
    map_confirm_password_reset_command,
    map_login_command,
    map_register_command,
    map_request_password_reset_command,
    map_resend_verification_command,
    map_update_profile_command,
    map_verify_email_command,
)

from backend.config import Settings
from backend.infrastructure.security.flask_protection import client_ip, rate_limit
from backend.infrastructure.web import flash, render_template
from backend.utils import log_security_event

auth_router = APIRouter(prefix="/auth")
auth_bp = auth_router

logger = logging.getLogger("anime_epic_moments")

UNAUTHORIZED = HTTPStatus.UNAUTHORIZED


@auth_router.get("/login", name="auth.login_page")
async def login_page(request: Request):
    """Render the login page.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered login page.
    """
    return render_template(request, "auth/login.html")


@auth_router.get("/register", name="auth.register_page")
async def register_page(request: Request):
    """Render the registration page.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered registration page.
    """
    return render_template(request, "auth/register.html")


@auth_router.get("/password-reset", name="auth.password_reset_request_page")
async def password_reset_request_page(request: Request):
    """Render the password reset request page.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered password reset request page.
    """
    return render_template(request, "auth/password_reset_request.html")


@auth_router.get("/verify-email", name="auth.verify_email_page")
async def verify_email_page(request: Request):
    """Render the email verification page.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered verification page.
    """
    return render_template(
        request,
        "auth/verify_email.html",
        email=str(request.query_params.get("email") or "").strip(),
    )


@auth_router.get("/password-reset/confirm", name="auth.password_reset_confirm_page")
async def password_reset_confirm_page(request: Request):
    """Render the password reset confirmation page.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered confirmation page.
    """
    token = str(request.query_params.get("token", ""))
    return render_template(request, "auth/password_reset_confirm.html", token=token)


@auth_router.post("/login", name="auth.login_user")
@rate_limit(
    scope="auth_login",
    limit=Settings.auth_login_attempts_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=lambda request: client_ip(request),
    response_mode="redirect",
    redirect_endpoint="auth.login_page",
)
async def login_user(request: Request):
    """Authenticate a user and set session cookies.

    Args:
        request: Incoming HTTP request.

    Returns:
        RedirectResponse: Redirect to the index page or back to login.
    """
    form = await request.form()
    try:
        command = map_login_command(form)
    except FormValidationError as error:
        flash(request, str(error))
        return redirect(request, "auth.login_page")
    result = await get_container(request).login_user_use_case().execute(
        email=command.email, password=command.password
    )
    if result.ok:
        log_security_event(
            event="login_success",
            user_id=str(result.data.id),
            email=command.email,
            ip_address=client_ip(request),
        )
    else:
        log_security_event(
            event="login_failed",
            email=command.email,
            ip_address=client_ip(request),
        )
    return resolve_auth(request, result)


@auth_router.post("/register", name="auth.register_user")
@rate_limit(
    scope="auth_register",
    limit=Settings.auth_register_attempts_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=lambda request: client_ip(request),
    response_mode="redirect",
    redirect_endpoint="auth.register_page",
)
async def register_user(request: Request):
    """Start registration by requesting an email verification code.

    Args:
        request: Incoming HTTP request.

    Returns:
        RedirectResponse: Redirect to the verification page or back.
    """
    form = await request.form()
    try:
        command = map_register_command(form)
    except FormValidationError as error:
        return redirect_verify(request, str(error))
    logger.info(
        "register_verification_requested email=%s ip=%s", command.email, client_ip(request)
    )
    result = await get_container(request).request_email_verification_use_case().execute(
        email=command.email,
        password=command.password,
        username=command.username,
        theme=command.theme,
    )
    return resolve_verify(request, result)


@auth_router.post("/verify-email", name="auth.verify_email")
async def verify_email(request: Request):
    """Verify an email verification code and complete registration.

    Args:
        request: Incoming HTTP request.

    Returns:
        RedirectResponse: Redirect to the index page on success.
    """
    form = await request.form()
    try:
        command = map_verify_email_command(form)
    except FormValidationError as error:
        return redirect_verify(request, str(error))
    result = await get_container(request).verify_email_use_case().execute(
        email=command.email, code=command.code
    )
    return resolve_auth(request, result)


@auth_router.post("/verify-email/resend", name="auth.resend_verification_email")
async def resend_verification_email(request: Request):
    """Resend the email verification code.

    Args:
        request: Incoming HTTP request.

    Returns:
        RedirectResponse: Redirect back to the verification page.
    """
    form = await request.form()
    try:
        command = map_resend_verification_command(form)
    except FormValidationError as error:
        return redirect_verify(request, str(error))
    log_security_event(
        event="email_verification_resend_requested",
        email=command.email,
        ip_address=client_ip(request),
    )
    result = await get_container(request).resend_email_verification_use_case().execute(
        email=command.email
    )
    return resolve_verify(request, result)


@auth_router.post("/password-reset", name="auth.request_password_reset")
async def request_password_reset(request: Request):
    """Request a password reset email for a user.

    Args:
        request: Incoming HTTP request.

    Returns:
        RedirectResponse: Redirect back to the password reset request page.
    """
    form = await request.form()
    try:
        command = map_request_password_reset_command(
            form, base_url=str(request.base_url).rstrip("/")
        )
    except FormValidationError:
        return redirect(request, "auth.password_reset_request_page")
    log_security_event(
        event="password_reset_requested",
        email=command.email,
        ip_address=client_ip(request),
    )
    await get_container(request).request_password_reset_use_case().execute(
        email=command.email, base_url=command.base_url
    )
    return redirect(request, "auth.password_reset_request_page")


@auth_router.post("/password-reset/confirm", name="auth.confirm_password_reset")
async def confirm_password_reset(request: Request):
    """Confirm a password reset with a token and new password.

    Args:
        request: Incoming HTTP request.

    Returns:
        RedirectResponse: Redirect to login on success.
    """
    form = await request.form()
    try:
        command = map_confirm_password_reset_command(form)
    except FormValidationError as error:
        return redirect_confirm(request, str(error))
    log_security_event(event="password_reset_success", ip_address=client_ip(request))
    result = await get_container(request).reset_password_use_case().execute(
        token=command.token, new_password=command.password
    )
    return resolve(request, result)


@auth_router.post("/logout", name="auth.logout_user")
async def logout_user(request: Request):
    """Clear the user session and revoke auth tokens.

    Args:
        request: Incoming HTTP request.

    Returns:
        RedirectResponse: Redirect to the index page.
    """
    await get_container(request).logout_user_use_case().execute(
        access_token=str(request.cookies.get("access_token") or "").strip(),
        refresh_token=str(request.cookies.get("refresh_token") or "").strip(),
    )
    response = redirect(request, "index.index")
    clear_auth_cookies(response)
    return response


@auth_router.post("/refresh", name="auth.refresh_session")
async def refresh_session(request: Request):
    """Rotate access and refresh tokens using a valid refresh cookie.

    Args:
        request: Incoming HTTP request.

    Returns:
        JSONResponse: Ok status with refreshed auth cookies.
    """
    result = await get_container(request).refresh_session_use_case().execute(
        str(request.cookies.get("refresh_token") or "").strip()
    )
    if not result.ok:
        return JSONResponse({"error": result.error_message}, status_code=UNAUTHORIZED)
    response = JSONResponse({"status": "ok"})
    set_auth_cookies(response, result.data)
    return response


@auth_router.get("/profile", name="auth.profile_page")
async def profile_page(request: Request):
    """Render the authenticated user's profile page.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered profile page.
    """
    user = getattr(request.state, "user", None)
    if not user:
        return redirect(request, "auth.login_page")
    overview = await get_container(request).get_profile_overview_use_case().execute(user.id)
    return render_template(
        request,
        "auth/profile.html",
        profile_user=user,
        profile_overview=overview,
    )


@auth_router.post("/profile", name="auth.update_profile")
async def update_profile(request: Request):
    """Update the authenticated user's profile.

    Args:
        request: Incoming HTTP request.

    Returns:
        RedirectResponse: Redirect back to the profile page.
    """
    user = getattr(request.state, "user", None)
    if not user:
        return redirect(request, "auth.login_page")
    form = await request.form()
    command = map_update_profile_command(form, user_id=user.id)
    result = await get_container(request).update_user_profile_use_case().execute(
        user_id=command.user_id,
        username=command.username,
        avatar_url=command.avatar_url,
    )
    return resolve(request, result)
