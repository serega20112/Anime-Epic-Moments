from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from src.backend.delivery.api.helpers import get_container, get_current_user, wants_json
from src.backend.infrastructure.security.flask_protection import client_ip, rate_limit
from src.backend.infrastructure.web.templating import flash, render_template

user_router = APIRouter(prefix="/users")
user_bp = user_router
container = None


@user_router.get("/{user_id}", name="user.public_profile_page")
async def public_profile_page(request: Request, user_id: int):
    container = get_container(request)
    viewer = get_current_user(request)
    try:
        public_profile = await container.get_public_profile_overview_use_case().execute(
            profile_user_id=user_id,
            viewer_user_id=viewer.id if viewer else None,
        )
    except ValueError:
        return render_template(request, "errors/500_modal.html", status_code=404)
    return render_template(
        request,
        "user/public_profile.html",
        public_profile=public_profile,
    )


@user_router.post("/{user_id}/follow", name="user.follow_user")
@rate_limit(
    scope="user_follow",
    limit=30,
    window_seconds=60,
    key_builder=lambda request: f"{client_ip(request)}::{getattr(get_current_user(request), 'id', 'guest')}",
)
async def follow_user(request: Request, user_id: int):
    container = get_container(request)
    viewer = get_current_user(request)
    if not viewer:
        return RedirectResponse(
            url=request.app.url_path_for("auth.login_page"),
            status_code=303,
        )
    try:
        state = await container.set_user_follow_use_case().execute(
            follower_user_id=viewer.id,
            followed_user_id=user_id,
            follow=True,
        )
    except ValueError as error:
        flash(request, str(error))
        return RedirectResponse(
            url=request.app.url_path_for("user.public_profile_page", user_id=str(user_id)),
            status_code=303,
        )
    if wants_json(request):
        return {"following": state}
    return RedirectResponse(
        url=request.app.url_path_for("user.public_profile_page", user_id=str(user_id)),
        status_code=303,
    )


@user_router.post("/{user_id}/unfollow", name="user.unfollow_user")
@rate_limit(
    scope="user_unfollow",
    limit=30,
    window_seconds=60,
    key_builder=lambda request: f"{client_ip(request)}::{getattr(get_current_user(request), 'id', 'guest')}",
)
async def unfollow_user(request: Request, user_id: int):
    container = get_container(request)
    viewer = get_current_user(request)
    if not viewer:
        return RedirectResponse(
            url=request.app.url_path_for("auth.login_page"),
            status_code=303,
        )
    try:
        state = await container.set_user_follow_use_case().execute(
            follower_user_id=viewer.id,
            followed_user_id=user_id,
            follow=False,
        )
    except ValueError as error:
        flash(request, str(error))
        return RedirectResponse(
            url=request.app.url_path_for("user.public_profile_page", user_id=str(user_id)),
            status_code=303,
        )
    if wants_json(request):
        return JSONResponse({"following": state})
    return RedirectResponse(
        url=request.app.url_path_for("user.public_profile_page", user_id=str(user_id)),
        status_code=303,
    )
