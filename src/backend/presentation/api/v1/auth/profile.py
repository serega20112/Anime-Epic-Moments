"""Authenticated user profile routes."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.use_cases.auth.profile.get_profile_overview import (
    GetProfileOverviewUseCase,
)
from backend.application.use_cases.auth.profile.update_user_profile import (
    UpdateUserProfileUseCase,
)
from backend.infrastructure.files.uploads import UploadValidationError, save_image
from backend.infrastructure.web import flash, render_template
from backend.presentation.api.auth_responses import redirect, resolve
from backend.presentation.api.requests.auth_mapper import map_update_profile_command

profile_router = APIRouter(route_class=DishkaRoute)


@profile_router.get("/profile", name="auth.profile_page")
async def profile_page(request: Request, use_case: FromDishka[GetProfileOverviewUseCase]):
    """Render the authenticated user's profile page.

    Args:
        request: Incoming HTTP request.
        use_case: Get profile overview use case.

    Returns:
        HTMLResponse: Rendered profile page.
    """
    user = getattr(request.state, "user", None)
    if not user:
        return await redirect(request, "auth.login_page")
    overview = await use_case.execute(user.id)
    return await render_template(
        request,
        "auth/profile.html",
        profile_user=user,
        profile_overview=overview,
    )


@profile_router.post("/profile", name="auth.update_profile")
async def update_profile(request: Request, use_case: FromDishka[UpdateUserProfileUseCase]):
    """Update the authenticated user's profile.

    Args:
        request: Incoming HTTP request.
        use_case: Update user profile use case.

    Returns:
        RedirectResponse: Redirect back to the profile page.
    """
    user = getattr(request.state, "user", None)
    if not user:
        return await redirect(request, "auth.login_page")
    form = await request.form()
    command = await map_update_profile_command(form, user_id=user.id)
    avatar_url = command.avatar_url
    avatar_upload = form.get("avatar_url")
    if hasattr(avatar_upload, "filename") and avatar_upload.filename:
        try:
            avatar_url = await save_image(avatar_upload, "avatars")
        except UploadValidationError as error:
            await flash(request, str(error))
            return await redirect(request, "auth.profile_page")
    result = await use_case.execute(
        user_id=command.user_id,
        username=command.username,
        avatar_url=avatar_url,
        status=command.status,
        show_watch_activity=command.show_watch_activity,
        show_recent_episodes=command.show_recent_episodes,
    )
    return await resolve(request, result)
