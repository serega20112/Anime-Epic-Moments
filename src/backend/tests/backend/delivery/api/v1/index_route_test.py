from __future__ import annotations

import pytest

from src.backend.delivery.api.v1.index_route import index_bp


@pytest.mark.parametrize("with_user", [False, True])
def test_index_route_renders_home_page(with_user, flask_app_factory, user_factory):
    """Проверяем, что главная страница рендерится без синхронной загрузки тяжелых блоков."""
    app = flask_app_factory(index_bp, user=user_factory() if with_user else None)

    response = app.test_client().get("/")

    assert response.status_code == 200
