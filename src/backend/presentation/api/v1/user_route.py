"""Thin HTTP routes for user profiles and follows."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from backend.infrastructure.security.flask_protection import client_ip, rate_limit
from backend.infrastructure.web import flash, render_template
from backend.presentation.api.helpers import get_container, get_current_user, wants_json

user_router = APIRouter(prefix="/users")
user_bp = user_router


def _login_redirect(request: Request) -> RedirectResponse:
    """Build a redirect to the login page.

    Args:
        request: Incoming HTTP request.

    Returns:
        RedirectResponse: SEE_OTHER redirect to login.
    """
    return RedirectResponse(
        url=request.app.url_path_for("auth.login_page"),
        status_code=HTTPStatus.SEE_OTHER,
    )


def _profile_redirect(request: Request, user_id: int) -> RedirectResponse:
    """Build a redirect back to the public profile page.

    Args:
        request: Incoming HTTP request.
        user_id: Profile user ID.

    Returns:
        RedirectResponse: SEE_OTHER redirect to the profile page.
    """
    return RedirectResponse(
        url=request.app.url_path_for(
            "user.public_profile_page",
            user_id=str(user_id),
        ),
        status_code=HTTPStatus.SEE_OTHER,
    )


@user_router.get("/{user_id}", name="user.public_profile_page")
async def public_profile_page(request: Request, user_id: int):
    """Render a user's public profile.

    Args:
        request: Incoming HTTP request.
        user_id: Profile user ID from path.

    Returns:
        HTMLResponse: Rendered public profile or 404 modal.
    """
    container = get_container(request)
    viewer = get_current_user(request)
    result = await container.get_public_profile_overview_use_case().execute(
        profile_user_id=user_id,
        viewer_user_id=viewer.id if viewer else None,
    )
    if not result.ok:
        return render_template(
            request,
            "errors/500_modal.html",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return render_template(
        request,
        "user/public_profile.html",
        public_profile=result.data,
    )


@user_router.post("/{user_id}/follow", name="user.follow_user")
@rate_limit(
    scope="user_follow",
    limit=30,
    window_seconds=60,
    key_builder=lambda request: (
            f"{client_ip(request)}::{getattr(get_current_user(request), 'id', 'guest')}"
    ),
)
async def follow_user(request: Request, user_id: int):
    """Follow a user.

    Args:
        request: Incoming HTTP request.
        user_id: Profile user ID from path.

    Returns:
        JSONResponse: Following state or an error.
        RedirectResponse: Redirect to the profile page.
    """
    return await _set_follow(request, user_id, follow=True)


@user_router.post("/{user_id}/unfollow", name="user.unfollow_user")
@rate_limit(
    scope="user_unfollow",
    limit=30,
    window_seconds=60,
    key_builder=lambda request: (
            f"{client_ip(request)}::{getattr(get_current_user(request), 'id', 'guest')}"
    ),
)
async def unfollow_user(request: Request, user_id: int):
    """Unfollow a user.

    Args:
        request: Incoming HTTP request.
        user_id: Profile user ID from path.

    Returns:
        JSONResponse: Following state or an error.
        RedirectResponse: Redirect to the profile page.
    """
    return await _set_follow(request, user_id, follow=False)


async def _set_follow(request: Request, user_id: int, *, follow: bool):
    """Shared follow/unfollow handler.

    Args:
        request: Incoming HTTP request.
        user_id: Profile user ID.
        follow: True to follow, False to unfollow.

    Returns:
        JSONResponse: Following state or an error.
        RedirectResponse: Redirect to the profile page.
    """
    viewer = get_current_user(request)
    if not viewer:
        return _login_redirect(request)
    container = get_container(request)
    result = await container.set_user_follow_use_case().execute(
        follower_user_id=viewer.id,
        followed_user_id=user_id,
        follow=follow,
    )
    if not result.ok:
        flash(request, result.error or "Не удалось обновить подписку")
        return _profile_redirect(request, user_id)
    if wants_json(request):
        return JSONResponse({"following": result.data})
    return _profile_redirect(request, user_id)
