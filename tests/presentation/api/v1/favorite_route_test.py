from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.presentation.api.v1 import favorite_route as favorite_route_module
from backend.presentation.api.v1.favorite_route import favorite_bp

@pytest.mark.parametrize(
    ("payload", "expected_status"),
    [
        ({"user_id": 1, "anime_id": 2}, 201),
        ({"user_id": 1}, 400),
        ({}, 400),
    ],
)
def test_add_favorite_route_validates_required_payload(payload, expected_status, flask_app_factory, monkeypatch):
    """Проверяем, что POST /favorites/ требует user_id и anime_id и принимает валидный payload."""
    add_use_case = SimpleNamespace(execute=lambda **kwargs: kwargs)
    monkeypatch.setattr(
        favorite_route_module,
        "container",
        SimpleNamespace(add_favorite_use_case=lambda: add_use_case),
    )
    app = flask_app_factory(favorite_bp)

    response = app.test_client().post("/favorites/", json=payload)

    assert response.status_code == expected_status

def test_add_favorite_route_forwards_snapshot_metadata(flask_app_factory, monkeypatch):
    """Проверяем, что POST /favorites/ передает snapshot-метаданные в use case."""
    captured = {}
    add_use_case = SimpleNamespace(execute=lambda **kwargs: captured.update(kwargs))
    monkeypatch.setattr(
        favorite_route_module,
        "container",
        SimpleNamespace(add_favorite_use_case=lambda: add_use_case),
    )
    app = flask_app_factory(favorite_bp)

    response = app.test_client().post(
        "/favorites/",
        json={
            "user_id": 1,
            "anime_id": 185,
            "title": "Initial D",
            "description": "desc",
            "cover_url": "cover",
            "genres": ["Action"],
        },
    )

    assert response.status_code == 201
    assert captured["title"] == "Initial D"
    assert captured["genres"] == ["Action"]

@pytest.mark.parametrize("payload", [{"user_id": 1, "anime_id": 2}, {"user_id": 1}, {}])
def test_remove_favorite_route_validates_payload(payload, flask_app_factory, monkeypatch):
    """Проверяем, что DELETE /favorites/ корректно валидирует обязательные поля."""
    remove_use_case = SimpleNamespace(execute=lambda **kwargs: kwargs)
    monkeypatch.setattr(
        favorite_route_module,
        "container",
        SimpleNamespace(remove_favorite_use_case=lambda: remove_use_case),
    )
    app = flask_app_factory(favorite_bp)

    response = app.test_client().delete("/favorites/", json=payload)

    expected_status = 204 if {"user_id", "anime_id"} <= payload.keys() else 400
    assert response.status_code == expected_status

def test_get_favorites_route_renders_page(flask_app_factory, monkeypatch):
    """Проверяем, что GET /favorites/<user_id> рендерит страницу избранного."""
    container = SimpleNamespace(
        get_favorites_use_case=lambda: SimpleNamespace(execute=lambda user_id: []),
        generate_recommendations_use_case=lambda: SimpleNamespace(execute=lambda user_id: []),
    )
    monkeypatch.setattr(favorite_route_module, "container", container)
    app = flask_app_factory(favorite_bp)

    response = app.test_client().get("/favorites/1")

    assert response.status_code == 200
