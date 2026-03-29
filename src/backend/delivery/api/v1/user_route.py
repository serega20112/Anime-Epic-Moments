from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, url_for

from src.backend.dependencies.container import container
from src.backend.infrastructure.security.flask_protection import client_ip, rate_limit

user_bp = Blueprint("user", __name__, url_prefix="/users")


@user_bp.route("/<int:user_id>", methods=["GET"])
def public_profile_page(user_id: int):
    """Рендерит публичный профиль пользователя с social-статистикой."""
    viewer = getattr(g, "user", None)
    try:
        public_profile = container.get_public_profile_overview_use_case().execute(
            profile_user_id=user_id,
            viewer_user_id=viewer.id if viewer else None,
        )
    except ValueError:
        return render_template("errors/500_modal.html"), 404
    return render_template("user/public_profile.html", public_profile=public_profile)


@user_bp.route("/<int:user_id>/follow", methods=["POST"])
@rate_limit(
    container_getter=lambda: container,
    scope="user_follow",
    limit=30,
    window_seconds=60,
    key_builder=lambda: f"{client_ip()}::{getattr(g, 'user', None).id if getattr(g, 'user', None) else 'guest'}",
)
def follow_user(user_id: int):
    """Подписывает текущего пользователя на другого пользователя."""
    viewer = getattr(g, "user", None)
    if not viewer:
        return redirect(url_for("auth.login_page"))
    try:
        state = container.set_user_follow_use_case().execute(
            follower_user_id=viewer.id,
            followed_user_id=user_id,
            follow=True,
        )
    except ValueError as error:
        flash(str(error))
        return redirect(url_for("user.public_profile_page", user_id=user_id))
    if request.is_json:
        return jsonify({"following": state})
    return redirect(url_for("user.public_profile_page", user_id=user_id))


@user_bp.route("/<int:user_id>/unfollow", methods=["POST"])
@rate_limit(
    container_getter=lambda: container,
    scope="user_unfollow",
    limit=30,
    window_seconds=60,
    key_builder=lambda: f"{client_ip()}::{getattr(g, 'user', None).id if getattr(g, 'user', None) else 'guest'}",
)
def unfollow_user(user_id: int):
    """Удаляет подписку текущего пользователя на другого пользователя."""
    viewer = getattr(g, "user", None)
    if not viewer:
        return redirect(url_for("auth.login_page"))
    try:
        state = container.set_user_follow_use_case().execute(
            follower_user_id=viewer.id,
            followed_user_id=user_id,
            follow=False,
        )
    except ValueError as error:
        flash(str(error))
        return redirect(url_for("user.public_profile_page", user_id=user_id))
    if request.is_json:
        return jsonify({"following": state})
    return redirect(url_for("user.public_profile_page", user_id=user_id))
