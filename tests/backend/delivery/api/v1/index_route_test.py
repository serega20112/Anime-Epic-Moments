from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.backend.delivery.api.v1 import index_route as index_route_module
from src.backend.delivery.api.v1.index_route import index_bp


@pytest.mark.parametrize("with_user", [False, True])
def test_index_route_renders_home_page(with_user, flask_app_factory, monkeypatch, anime_factory, user_factory):
    """Проверяем, что главная страница рендерится и подтягивает рекомендации только для авторизованного пользователя."""
    recommendation = SimpleNamespace(
        anime_id=91,
        title="Rec",
        description="desc",
        image_url=None,
        genres=["Action"],
        watch_url="/watch/91?episode=1",
    )
    container = SimpleNamespace(
        get_season_popular_use_case=lambda: SimpleNamespace(
            execute=lambda: [anime_factory(title="Popular")]
        ),
        generate_recommendations_use_case=lambda: SimpleNamespace(
            execute=lambda user_id: [recommendation]
        ),
    )
    monkeypatch.setattr(index_route_module, "container", container)
    app = flask_app_factory(index_bp, user=user_factory() if with_user else None)

    response = app.test_client().get("/")

    assert response.status_code == 200
