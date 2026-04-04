from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from src.backend.dependencies import auth_dependencies as auth_dependencies_module


def _build_app():
    app = FastAPI()

    @app.get("/protected")
    @auth_dependencies_module.auth_required
    async def protected(_request: Request, user_id: int):
        return JSONResponse({"user_id": user_id})

    return app


def test_auth_required_rejects_missing_token(monkeypatch):
    """Проверяем, что auth_required возвращает 401, если Authorization header отсутствует."""
    monkeypatch.setattr(auth_dependencies_module.jwt_service, "decode_token", lambda token: 1)
    app = _build_app()

    with TestClient(app) as client:
        response = client.get("/protected")

    assert response.status_code == 401
    assert response.json() == {"error": "Authorization token required"}


def test_auth_required_rejects_invalid_token(monkeypatch):
    """Проверяем, что auth_required возвращает 401, если токен не проходит декодирование."""
    monkeypatch.setattr(
        auth_dependencies_module.jwt_service,
        "decode_token",
        lambda token: (_ for _ in ()).throw(ValueError("bad token")),
    )
    app = _build_app()

    with TestClient(app) as client:
        response = client.get(
            "/protected",
            headers={"Authorization": "invalid-token"},
        )

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or expired token"}


def test_auth_required_passes_decoded_user_id(monkeypatch):
    """Проверяем, что auth_required пробрасывает декодированный user_id в endpoint."""
    monkeypatch.setattr(auth_dependencies_module.jwt_service, "decode_token", lambda token: 77)
    app = _build_app()

    with TestClient(app) as client:
        response = client.get(
            "/protected",
            headers={"Authorization": "valid-token"},
        )

    assert response.status_code == 200
    assert response.json() == {"user_id": 77}
