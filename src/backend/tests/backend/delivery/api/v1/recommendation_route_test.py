from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.backend.delivery.api.v1 import recommendation_route as recommendation_route_module
from src.backend.delivery.api.v1.recommendation_route import recommendation_bp


@pytest.mark.parametrize(
    ("path", "factory_name"),
    [
        ("/api/v1/recommendations/generate/1", "generate_recommendations_use_case"),
        ("/api/v1/recommendations/refresh/1", "refresh_recommendations_use_case"),
    ],
)
def test_recommendation_routes_return_serialized_items(path, factory_name, flask_app_factory, monkeypatch):
    """Проверяем, что recommendation endpoints отдают JSON из RecommendationResult-подобных объектов."""
    container = SimpleNamespace(
        generate_recommendations_use_case=lambda: SimpleNamespace(
            execute=lambda user_id: [SimpleNamespace(anime_id=1, title="A")]
        ),
        refresh_recommendations_use_case=lambda: SimpleNamespace(
            execute=lambda user_id: [SimpleNamespace(anime_id=2, title="B")]
        ),
    )
    monkeypatch.setattr(recommendation_route_module, "container", container)
    app = flask_app_factory(recommendation_bp)

    response = app.test_client().post(path)

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_ask_ai_recommendations_route_returns_serialized_items(flask_app_factory, monkeypatch):
    """Проверяем, что AI recommendation endpoint отдает JSON для текстового запроса пользователя."""
    container = SimpleNamespace(
        generate_recommendations_use_case=lambda: SimpleNamespace(execute=lambda user_id: []),
        refresh_recommendations_use_case=lambda: SimpleNamespace(execute=lambda user_id: []),
        ask_ai_recommendations_use_case=lambda: SimpleNamespace(
            execute=lambda user_id, query, limit=6: [
                SimpleNamespace(anime_id=3, title="Bleach", reason="query match")
            ]
        ),
    )
    monkeypatch.setattr(recommendation_route_module, "container", container)
    app = flask_app_factory(recommendation_bp)

    response = app.test_client().post(
        "/api/v1/recommendations/ask/1",
        json={"query": "как Naruto, но темнее"},
    )

    assert response.status_code == 200
    assert response.get_json()[0]["anime_id"] == 3
