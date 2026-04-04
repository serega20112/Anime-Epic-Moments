from __future__ import annotations

from types import SimpleNamespace

from src.backend.delivery.api.v1 import support_route as support_route_module
from src.backend.delivery.api.v1.index_route import index_bp
from src.backend.delivery.api.v1.support_route import support_bp


def test_support_page_renders_successfully(flask_app_factory, monkeypatch):
    """Проверяем, что support-страница открывается без ошибок."""
    monkeypatch.setattr(support_route_module, "container", SimpleNamespace())
    app = flask_app_factory(support_bp, index_bp)

    response = app.test_client().get("/support")

    assert response.status_code == 200
    assert "Telegram".encode("utf-8") in response.data
    assert "Email".encode("utf-8") in response.data


def test_create_support_ticket_uses_authenticated_user_data(
    flask_app_factory,
    monkeypatch,
    user_factory,
):
    """Проверяем, что авторизованный пользователь не обязан повторно вводить email и username."""
    captured = {}

    def _execute(**payload):
        captured.update(payload)
        return SimpleNamespace(
            id=11,
            user_id=payload["user_id"],
            channel=payload["channel"],
            delivery_status="sent",
        )

    monkeypatch.setattr(
        support_route_module,
        "container",
        SimpleNamespace(create_support_ticket_use_case=lambda: SimpleNamespace(execute=_execute)),
    )
    app = flask_app_factory(support_bp, index_bp, user=user_factory(id=5, email="me@example.com", username="neo"))

    response = app.test_client().post(
        "/support",
        data={
            "channel": "email",
            "subject": "Не работает серия",
            "message": "Плеер не запускается и остается черный экран.",
            "page_url": "https://example.com/watch/7",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/support")
    assert captured == {
        "user_id": 5,
        "email": "me@example.com",
        "username": "neo",
        "subject": "Не работает серия",
        "message": "Плеер не запускается и остается черный экран.",
        "channel": "email",
        "page_url": "https://example.com/watch/7",
    }


def test_create_support_ticket_returns_validation_error_for_guest(
    flask_app_factory,
    monkeypatch,
):
    """Проверяем, что guest получает 400 и остается на support-странице при ошибке валидации."""
    monkeypatch.setattr(
        support_route_module,
        "container",
        SimpleNamespace(
            create_support_ticket_use_case=lambda: SimpleNamespace(
                execute=lambda **payload: (_ for _ in ()).throw(
                    support_route_module.InvalidSupportTicketError("Некорректный email")
                )
            )
        ),
    )
    app = flask_app_factory(support_bp, index_bp)

    response = app.test_client().post(
        "/support",
        data={
            "email": "bad-email",
            "username": "guest",
            "channel": "telegram",
            "subject": "Проблема с входом",
            "message": "Не могу зайти в аккаунт через форму входа.",
        },
    )

    assert response.status_code == 400
    assert "Некорректный email".encode("utf-8") in response.data
