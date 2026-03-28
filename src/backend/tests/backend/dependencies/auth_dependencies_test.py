from __future__ import annotations

from flask import Flask, jsonify

from src.backend.dependencies import auth_dependencies as auth_dependencies_module


def _build_app():
    app = Flask(__name__)
    app.config.update(TESTING=True)

    @app.get("/protected")
    @auth_dependencies_module.auth_required
    def protected(user_id):
        return jsonify({"user_id": user_id})

    return app


def test_auth_required_rejects_missing_token(monkeypatch):
    """Проверяем, что auth_required возвращает 401, если Authorization header отсутствует."""
    monkeypatch.setattr(auth_dependencies_module.jwt_service, "decode_token", lambda token: 1)
    app = _build_app()

    response = app.test_client().get("/protected")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Authorization token required"}


def test_auth_required_rejects_invalid_token(monkeypatch):
    """Проверяем, что auth_required возвращает 401, если токен не проходит декодирование."""
    monkeypatch.setattr(
        auth_dependencies_module.jwt_service,
        "decode_token",
        lambda token: (_ for _ in ()).throw(ValueError("bad token")),
    )
    app = _build_app()

    response = app.test_client().get(
        "/protected",
        headers={"Authorization": "invalid-token"},
    )

    assert response.status_code == 401
    assert response.get_json() == {"error": "Invalid or expired token"}


def test_auth_required_passes_decoded_user_id(monkeypatch):
    """Проверяем, что auth_required пробрасывает декодированный user_id в endpoint."""
    monkeypatch.setattr(auth_dependencies_module.jwt_service, "decode_token", lambda token: 77)
    app = _build_app()

    response = app.test_client().get(
        "/protected",
        headers={"Authorization": "valid-token"},
    )

    assert response.status_code == 200
    assert response.get_json() == {"user_id": 77}
