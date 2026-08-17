"""HTTP response helpers for authentication routes.

These helpers translate use case results (:class:`AuthResult`) and raw request
data into redirects, cookies and flash messages. They keep the route handlers
thin and free of error-handling logic.
"""

from __future__ import annotations

from http import HTTPStatus

from fastapi import Request
from fastapi.responses import RedirectResponse

from backend.application.use_cases.auth.result import AuthResult
from backend.config import Settings
from backend.infrastructure.security.jwt_service import JWTService
from backend.infrastructure.web import flash

SEE_OTHER = HTTPStatus.SEE_OTHER

jwt_service = JWTService()


async def resolve(request: Request, result: AuthResult) -> RedirectResponse:
    """Apply a plain success/failure redirect result.

    Args:
        request: Incoming HTTP request.
        result: Use case result.

    Returns:
        RedirectResponse: Redirect according to the result.
    """
    if result.ok:
        if result.message:
            await flash(request, result.message)
        return await redirect(request, result.redirect_endpoint or "index.index")
    await flash(request, result.error_message or "")
    return await redirect(request, result.error_endpoint or "auth.login_page")


async def resolve_auth(request: Request, result: AuthResult) -> RedirectResponse:
    """Apply an auth result, setting JWT cookies on success.

    Args:
        request: Incoming HTTP request.
        result: Use case result.

    Returns:
        RedirectResponse: Redirect with optional cookies set.
    """
    if result.ok:
        if result.message:
            await flash(request, result.message)
        response = await redirect(request, result.redirect_endpoint or "index.index")
        if result.data is not None:
            await set_auth_cookies(response, result.data.id)
        return response
    await flash(request, result.error_message or "")
    return await redirect(request, result.error_endpoint or "auth.login_page")


async def resolve_verify(request: Request, result: AuthResult) -> RedirectResponse:
    """Apply a redirect toward the email verification page.

    Args:
        request: Incoming HTTP request.
        result: Use case result.

    Returns:
        RedirectResponse: Redirect preserving the email query parameter.
    """
    if result.ok:
        if result.message:
            await flash(request, result.message)
        return await redirect_verify(request, result.redirect_email)
    await flash(request, result.error_message or "")
    return await redirect_verify(request, result.redirect_email)


async def redirect(request: Request, endpoint: str) -> RedirectResponse:
    """Build a see-other redirect to a named route.

    Args:
        request: Incoming HTTP request.
        endpoint: Named route endpoint.

    Returns:
        RedirectResponse: SEE_OTHER redirect.
    """
    return RedirectResponse(
        url=request.app.url_path_for(endpoint),
        status_code=SEE_OTHER,
    )


async def redirect_verify(request: Request, email) -> RedirectResponse:
    """Build a redirect to the verify email page preserving the email.

    Args:
        request: Incoming HTTP request.
        email: Submitted email.

    Returns:
        RedirectResponse: SEE_OTHER redirect.
    """
    return RedirectResponse(
        url=(
            f"{request.app.url_path_for('auth.verify_email_page')}"
            f"?email={str(email or '').strip().lower()}"
        ),
        status_code=SEE_OTHER,
    )


async def redirect_confirm(request: Request, token) -> RedirectResponse:
    """Build a redirect to the confirm password reset page.

    Args:
        request: Incoming HTTP request.
        token: Password reset token.

    Returns:
        RedirectResponse: SEE_OTHER redirect.
    """
    return RedirectResponse(
        url=(
            f"{request.app.url_path_for('auth.password_reset_confirm_page')}"
            f"?token={str(token or '').strip()}"
        ),
        status_code=SEE_OTHER,
    )


async def set_auth_cookies(response, user_id: int):
    """Set access and refresh JWT cookies on the response.

    Args:
        response: HTTP response to attach cookies to.
        user_id: Authenticated user identifier.
    """
    access_token = await jwt_service.create_access_token(user_id)
    refresh_token = await jwt_service.create_refresh_token(user_id)
    cookie_kwargs = {
        "httponly": True,
        "secure": Settings.cookie_secure,
        "samesite": Settings.cookie_samesite,
        "path": "/",
    }
    if Settings.cookie_domain:
        cookie_kwargs["domain"] = Settings.cookie_domain
    response.set_cookie(
        "access_token",
        access_token,
        max_age=Settings.access_token_expire_minutes * 60,
        **cookie_kwargs,
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=Settings.refresh_token_expire_days * 86400,
        **cookie_kwargs,
    )


async def clear_auth_cookies(response):
    """Clear the auth cookies on the response.

    Args:
        response: HTTP response to delete cookies from.
    """
    cookie_kwargs = {
        "httponly": True,
        "secure": Settings.cookie_secure,
        "samesite": Settings.cookie_samesite,
        "path": "/",
    }
    if Settings.cookie_domain:
        cookie_kwargs["domain"] = Settings.cookie_domain
    response.delete_cookie("access_token", **cookie_kwargs)
    response.delete_cookie("refresh_token", **cookie_kwargs)
