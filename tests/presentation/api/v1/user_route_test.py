from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.presentation.api.v1 import user_route as user_route_module
from backend.presentation.api.v1.user_route import user_bp

def test_public_profile_page_renders_for_existing_user(flask_app_factory, monkeypatch):
    """Проверяем, что публичный профиль пользователя рендерится при валидном payload use case."""
    monkeypatch.setattr(
        user_route_module,
        "container",
        SimpleNamespace(
            get_public_profile_overview_use_case=lambda: SimpleNamespace(
                execute=lambda **kwargs: SimpleNamespace(
                    profile=SimpleNamespace(
                        user_id=7,
                        username="public-user",
                        avatar_url=None,
                        created_at="2026-03-21",
                        summary=SimpleNamespace(highlight_count=4, like_count=0, saved_count=0),
                        smart_profile=SimpleNamespace(
                            favorite_genres=[],
                            dominant_mood=SimpleNamespace(
                                label="Экшен",
                                description="desc",
                                emoji="🔥",
                            ),
                            average_rating=8.9,
                            hours_watched=12.0,
                            top_anime=[],
                            heatmap=[],
                            achievements=[],
                            ai_taste_summary="summary",
                        ),
                        popular_highlights=[],
                        recent_highlights=[],
                    ),
                    public_collections=[],
                    followers_preview=[],
                    following_preview=[],
                    followers_count=3,
                    following_count=2,
                    is_following=False,
                    can_follow=False,
                )
            )
        ),
    )
    app = flask_app_factory(user_bp)

    response = app.test_client().get("/users/7")

    assert response.status_code == 200

@pytest.mark.parametrize(
    ("path", "has_user", "expected_status"),
    [
        ("/users/7/follow", False, 302),
        ("/users/7/follow", True, 302),
        ("/users/7/unfollow", True, 302),
    ],
)
def test_follow_routes_require_auth_and_redirect_back(
    path,
    has_user,
    expected_status,
    flask_app_factory,
    monkeypatch,
    user_factory,
):
    """Проверяем, что follow и unfollow либо требуют логин, либо возвращают на публичный профиль."""
    monkeypatch.setattr(
        user_route_module,
        "container",
        SimpleNamespace(
            set_user_follow_use_case=lambda: SimpleNamespace(execute=lambda **kwargs: True),
        ),
    )
    app = flask_app_factory(user_bp, user=user_factory() if has_user else None)

    response = app.test_client().post(path)

    assert response.status_code == expected_status
    assert response.headers["Location"].endswith("/auth/login" if not has_user else "/users/7")
