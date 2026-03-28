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
    monkeypatch.setattr(auth_route_module.jwt_service, "create_token", lambda user_id: f"token-{user_id}")
    app = flask_app_factory(auth_bp, index_bp)

    response = app.test_client().post(
        "/auth/login",
        data={"email": "user@example.com", "password": "password123"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert "access_token=token-9" in response.headers.get("Set-Cookie", "")


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


@pytest.mark.parametrize("user_present, expected_status", [(False, 302), (True, 200)])
def test_profile_page_requires_authenticated_user(
    user_present,
    expected_status,
    flask_app_factory,
    monkeypatch,
    user_factory,
):
    """Проверяем, что профиль доступен только авторизованному пользователю."""
    monkeypatch.setattr(auth_route_module, "container", SimpleNamespace())
    app = flask_app_factory(auth_bp, index_bp, user=user_factory() if user_present else None)

    response = app.test_client().get("/auth/profile")

    assert response.status_code == expected_status
