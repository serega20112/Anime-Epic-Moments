"""Thin HTTP routes for user profiles and follows."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from backend.application.use_cases import GetPublicProfileOverviewUseCase, SetUserFollowUseCase
from backend.infrastructure.security.flask_protection import client_ip, rate_limit
from backend.infrastructure.web import flash, render_template
from backend.presentation.api.helpers import get_current_user, wants_json

user_router = APIRouter(prefix="/users", route_class=DishkaRoute)
user_bp = user_router


async def _follow_subject(request: Request) -> str:
    """Build a composite rate-limit subject for follow actions."""
    ip = await client_ip(request)
    user_id = getattr(await get_current_user(request), "id", "guest")
    return f"{ip}::{user_id}"


async def _login_redirect(request: Request) -> RedirectResponse:
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


async def _profile_redirect(request: Request, user_id: int) -> RedirectResponse:
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
async def public_profile_page(
    request: Request,
    user_id: int,
    use_case: FromDishka[GetPublicProfileOverviewUseCase],
):
    """Render a user's public profile.

    Args:
        request: Incoming HTTP request.
        user_id: Profile user ID from path.
        use_case: Get public profile overview use case.

    Returns:
        HTMLResponse: Rendered public profile or 404 modal.
    """
    viewer = await get_current_user(request)
    result = await use_case.execute(
        profile_user_id=user_id,
        viewer_user_id=viewer.id if viewer else None,
    )
    if not result.ok:
        return await render_template(
            request,
            "errors/500_modal.html",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return await render_template(
        request,
        "user/public_profile.html",
        public_profile=result.data,
    )


@user_router.post("/{user_id}/follow", name="user.follow_user")
@rate_limit(
    scope="user_follow",
    limit=30,
    window_seconds=60,
    key_builder=_follow_subject,
)
async def follow_user(
    request: Request,
    user_id: int,
    use_case: FromDishka[SetUserFollowUseCase],
):
    """Follow a user.

    Args:
        request: Incoming HTTP request.
        user_id: Profile user ID from path.
        use_case: Set user follow use case.

    Returns:
        JSONResponse: Following state or an error.
        RedirectResponse: Redirect to the profile page.
    """
    return await _set_follow(request, user_id, follow=True, use_case=use_case)


@user_router.post("/{user_id}/unfollow", name="user.unfollow_user")
@rate_limit(
    scope="user_unfollow",
    limit=30,
    window_seconds=60,
    key_builder=_follow_subject,
)
async def unfollow_user(
    request: Request,
    user_id: int,
    use_case: FromDishka[SetUserFollowUseCase],
):
    """Unfollow a user.

    Args:
        request: Incoming HTTP request.
        user_id: Profile user ID from path.
        use_case: Set user follow use case.

    Returns:
        JSONResponse: Following state or an error.
        RedirectResponse: Redirect to the profile page.
    """
    return await _set_follow(request, user_id, follow=False, use_case=use_case)


async def _set_follow(
    request: Request,
    user_id: int,
    *,
    follow: bool,
    use_case: SetUserFollowUseCase,
):
    """Shared follow/unfollow handler.

    Args:
        request: Incoming HTTP request.
        user_id: Profile user ID.
        follow: True to follow, False to unfollow.
        use_case: Set user follow use case.

    Returns:
        JSONResponse: Following state or an error.
        RedirectResponse: Redirect to the profile page.
    """
    viewer = await get_current_user(request)
    if not viewer:
        return await _login_redirect(request)
    result = await use_case.execute(
        follower_user_id=viewer.id,
        followed_user_id=user_id,
        follow=follow,
    )
    if not result.ok:
        await flash(request, result.error or "Не удалось обновить подписку")
        return await _profile_redirect(request, user_id)
    if await wants_json(request):
        return JSONResponse({"following": result.data})
    return await _profile_redirect(request, user_id)
