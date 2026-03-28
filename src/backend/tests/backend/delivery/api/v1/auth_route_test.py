from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.backend.delivery.api.v1 import auth_route as auth_route_module
from src.backend.delivery.api.v1.auth_route import auth_bp
from src.backend.delivery.api.v1.index_route import index_bp
from src.backend.use_case.auth.login_user import InvalidCredentialsError


@pytest.mark.parametrize(
    "path",
    [
        "/auth/login",
        "/auth/register",
        "/auth/password-reset",
        "/auth/verify-email?email=user@example.com",
        "/auth/password-reset/confirm?token=test-token",
    ],
)
def test_auth_pages_render_successfully(path, flask_app_factory, monkeypatch):
    """Проверяем, что публичные auth-страницы рендерятся без ошибок."""
    monkeypatch.setattr(auth_route_module, "container", SimpleNamespace())
    app = flask_app_factory(auth_bp, index_bp)

    response = app.test_client().get(path)

    assert response.status_code == 200


def test_login_user_sets_cookie_and_redirects(flask_app_factory, monkeypatch, user_factory):
    """Проверяем, что успешный логин ставит access_token и редиректит на главную."""
    login_use_case = SimpleNamespace(execute=lambda email, password: user_factory(id=9))
    monkeypatch.setattr(
        auth_route_module,
        "container",
        SimpleNamespace(login_user_use_case=lambda: login_use_case),
    )
    monkeypatch.setattr(
        auth_route_module.jwt_service,
        "create_access_token",
        lambda user_id: f"access-{user_id}",
    )
    monkeypatch.setattr(
        auth_route_module.jwt_service,
        "create_refresh_token",
        lambda user_id: f"refresh-{user_id}",
    )
    app = flask_app_factory(auth_bp, index_bp)

    response = app.test_client().post(
        "/auth/login",
        data={"email": "user@example.com", "password": "password123"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    set_cookie_header = "\n".join(response.headers.getlist("Set-Cookie"))
    assert "access_token=access-9" in set_cookie_header
    assert "refresh_token=refresh-9" in set_cookie_header


def test_login_user_redirects_back_on_invalid_credentials(flask_app_factory, monkeypatch):
    """Проверяем, что неверные логин и пароль возвращают на страницу входа."""
    login_use_case = SimpleNamespace(
        execute=lambda email, password: (_ for _ in ()).throw(InvalidCredentialsError("bad credentials"))
    )
    monkeypatch.setattr(
        auth_route_module,
        "container",
        SimpleNamespace(login_user_use_case=lambda: login_use_case),
    )
    app = flask_app_factory(auth_bp, index_bp)

    response = app.test_client().post(
        "/auth/login",
        data={"email": "user@example.com", "password": "bad"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")


def test_register_user_requests_email_verification_and_redirects(flask_app_factory, monkeypatch):
    """Проверяем, что регистрация запускает email verification и ведет на ввод кода без выдачи JWT."""
    request_verification_use_case = SimpleNamespace(
        execute=lambda email, password, username, theme: SimpleNamespace(
            email=email,
            username=username,
            theme=theme,
        )
    )
    monkeypatch.setattr(
        auth_route_module,
        "container",
        SimpleNamespace(
            request_email_verification_use_case=lambda: request_verification_use_case,
        ),
    )
    app = flask_app_factory(auth_bp, index_bp)

    response = app.test_client().post(
        "/auth/register",
        data={
            "email": "user@example.com",
            "password": "password123",
            "username": "tester",
            "theme": "dark",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/auth/verify-email?email=user@example.com"
    )
    set_cookie_header = "\n".join(response.headers.getlist("Set-Cookie"))
    assert "access_token=" not in set_cookie_header
    assert "refresh_token=" not in set_cookie_header


def test_verify_email_sets_auth_cookies_and_redirects(flask_app_factory, monkeypatch, user_factory):
    """Проверяем, что подтверждение email завершает регистрацию, ставит JWT и ведет на главную."""
    verify_email_use_case = SimpleNamespace(
        execute=lambda email, code: user_factory(id=15, username="verified-user")
    )
    monkeypatch.setattr(
        auth_route_module,
        "container",
        SimpleNamespace(
            verify_email_use_case=lambda: verify_email_use_case,
        ),
    )
    monkeypatch.setattr(
        auth_route_module.jwt_service,
        "create_access_token",
        lambda user_id: f"access-{user_id}",
    )
    monkeypatch.setattr(
        auth_route_module.jwt_service,
        "create_refresh_token",
        lambda user_id: f"refresh-{user_id}",
    )
    app = flask_app_factory(auth_bp, index_bp)

    response = app.test_client().post(
        "/auth/verify-email",
        data={"email": "user@example.com", "code": "123456"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    set_cookie_header = "\n".join(response.headers.getlist("Set-Cookie"))
    assert "access_token=access-15" in set_cookie_header
    assert "refresh_token=refresh-15" in set_cookie_header


def test_resend_verification_email_redirects_back_to_verify_page(flask_app_factory, monkeypatch):
    """Проверяем, что повторная отправка кода возвращает пользователя на страницу подтверждения email."""
    resend_use_case = SimpleNamespace(execute=lambda email: SimpleNamespace(email=email))
    monkeypatch.setattr(
        auth_route_module,
        "container",
        SimpleNamespace(
            resend_email_verification_use_case=lambda: resend_use_case,
        ),
    )
    app = flask_app_factory(auth_bp, index_bp)

    response = app.test_client().post(
        "/auth/verify-email/resend",
        data={"email": "user@example.com"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/auth/verify-email?email=user@example.com"
    )


@pytest.mark.parametrize("user_present, expected_status", [(False, 302), (True, 200)])
def test_profile_page_requires_authenticated_user(
    user_present,
    expected_status,
    flask_app_factory,
    monkeypatch,
    user_factory,
):
    """Проверяем, что профиль доступен только авторизованному пользователю."""
    monkeypatch.setattr(
        auth_route_module,
        "container",
        SimpleNamespace(
            get_profile_overview_use_case=lambda: SimpleNamespace(
                execute=lambda user_id: SimpleNamespace(
                    user_id=user_id,
                    email="user@example.com",
                    username="tester",
                    avatar_url=None,
                    created_at="2026-03-20",
                    summary=SimpleNamespace(highlight_count=0, like_count=0, saved_count=0),
                    recent_highlights=[],
                    popular_highlights=[],
                    liked_highlights=[],
                    saved_highlights=[],
                    recent_activity=[],
                    smart_profile=SimpleNamespace(
                        favorite_genres=[],
                        dominant_mood=SimpleNamespace(
                            label="Смешанный вкус",
                            description="desc",
                            emoji="🎭",
                        ),
                        average_rating=None,
                        hours_watched=0.0,
                        top_anime=[],
                        heatmap=[],
                        achievements=[],
                        ai_taste_summary="summary",
                    ),
                )
            )
        ),
    )
    app = flask_app_factory(auth_bp, index_bp, user=user_factory() if user_present else None)

    response = app.test_client().get("/auth/profile")

    assert response.status_code == expected_status


def test_refresh_session_rotates_tokens(flask_app_factory, monkeypatch):
    """Проверяем, что /auth/refresh перевыпускает access и refresh token по валидному refresh cookie."""
    monkeypatch.setattr(
        auth_route_module,
        "container",
        SimpleNamespace(token_blocklist=SimpleNamespace(is_revoked=lambda token: False, revoke=lambda token, ttl: None)),
    )
    monkeypatch.setattr(auth_route_module.jwt_service, "decode_refresh_token", lambda token: 11)
    monkeypatch.setattr(
        auth_route_module.jwt_service,
        "get_token_ttl_seconds",
        lambda token, expected_type=None: 120,
    )
    monkeypatch.setattr(
        auth_route_module.jwt_service,
        "create_access_token",
        lambda user_id: f"access-{user_id}",
    )
    monkeypatch.setattr(
        auth_route_module.jwt_service,
        "create_refresh_token",
        lambda user_id: f"refresh-{user_id}",
    )
    app = flask_app_factory(auth_bp, index_bp)
    client = app.test_client()
    client.set_cookie("refresh_token", "refresh-old")

    response = client.post("/auth/refresh")

    assert response.status_code == 200
    set_cookie_header = "\n".join(response.headers.getlist("Set-Cookie"))
    assert "access_token=access-11" in set_cookie_header
    assert "refresh_token=refresh-11" in set_cookie_header
