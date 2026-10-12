"""Session routes: login, register, logout, refresh tokens."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.application.use_cases import LogoutUserUseCase, RefreshSessionUseCase
from backend.application.use_cases.auth.login_register.login_user import LoginUserUseCase
from backend.application.use_cases.auth.verification.request_email_verification import (
    RequestEmailVerificationUseCase,
)
from backend.config import Settings
from backend.infrastructure.security import client_ip
from backend.infrastructure.web import flash, render_template
from backend.presentation.api import rate_limit
from backend.presentation.api.auth_responses import (
    clear_auth_cookies,
    redirect,
    redirect_verify,
    resolve_auth,
    resolve_verify,
    set_auth_cookies,
)
from backend.presentation.api.requests.auth_mapper import (
    FormValidationError,
    map_login_command,
    map_register_command,
)

session_router = APIRouter(route_class=DishkaRoute)

UNAUTHORIZED = HTTPStatus.UNAUTHORIZED


@session_router.get("/login", name="auth.login_page")
async def login_page(request: Request):
    """Render the login page.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered login page.
    """
    return await render_template(request, "auth/login.html")


@session_router.get("/register", name="auth.register_page")
async def register_page(request: Request):
    """Render the registration page.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered registration page.
    """
    return await render_template(request, "auth/register.html")


@session_router.post("/login", name="auth.login_user")
@rate_limit(
    scope="auth_login",
    limit=Settings.auth_login_attempts_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=lambda request: client_ip(request),
    response_mode="redirect",
    redirect_endpoint="auth.login_page",
)
async def login_user(request: Request, use_case: FromDishka[LoginUserUseCase]):
    """Authenticate a user and set session cookies.

    Args:
        request: Incoming HTTP request.
        use_case: Login user use case.

    Returns:
        RedirectResponse: Redirect to the index page or back to login.
    """
    form = await request.form()
    try:
        command = await map_login_command(form)
    except FormValidationError as error:
        await flash(request, str(error))
        return await redirect(request, "auth.login_page")
    result = await use_case.execute(
        email=command.email,
        password=command.password,
        ip_address=await client_ip(request),
    )
    return await resolve_auth(request, result)


@session_router.post("/register", name="auth.register_user")
@rate_limit(
    scope="auth_register",
    limit=Settings.auth_register_attempts_limit,
    window_seconds=Settings.auth_window_seconds,
    key_builder=lambda request: client_ip(request),
    response_mode="redirect",
    redirect_endpoint="auth.register_page",
)
async def register_user(request: Request, use_case: FromDishka[RequestEmailVerificationUseCase]):
    """Start registration by requesting an email verification code.

    Args:
        request: Incoming HTTP request.
        use_case: Request email verification use case.

    Returns:
        RedirectResponse: Redirect to the verification page or back.
    """
    form = await request.form()
    try:
        command = await map_register_command(form)
    except FormValidationError as error:
        return await redirect_verify(request, str(error))
    result = await use_case.execute(
        email=command.email,
        password=command.password,
        username=command.username,
        theme=command.theme,
    )
    return await resolve_verify(request, result)


@session_router.post("/logout", name="auth.logout_user")
async def logout_user(request: Request, use_case: FromDishka[LogoutUserUseCase]):
    """Clear the user session and revoke auth tokens.

    Args:
        request: Incoming HTTP request.
        use_case: Logout user use case.

    Returns:
        RedirectResponse: Redirect to the index page.
    """
    await use_case.execute(
        access_token=str(request.cookies.get("access_token") or "").strip(),
        refresh_token=str(request.cookies.get("refresh_token") or "").strip(),
    )
    response = await redirect(request, "index.index")
    await clear_auth_cookies(response)
    return response


@session_router.post("/refresh", name="auth.refresh_session")
async def refresh_session(request: Request, use_case: FromDishka[RefreshSessionUseCase]):
    """Rotate access and refresh tokens using a valid refresh cookie.

    Args:
        request: Incoming HTTP request.
        use_case: Refresh session use case.

    Returns:
        JSONResponse: Ok status with refreshed auth cookies.
    """
    result = await use_case.execute(str(request.cookies.get("refresh_token") or "").strip())
    if not result.ok:
        return JSONResponse({"error": result.error_message}, status_code=UNAUTHORIZED)
    response = JSONResponse({"status": "ok"})
    await set_auth_cookies(response, request, result.data.id)
    return response
