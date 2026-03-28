from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.backend.delivery.api.v1 import highlight_route as highlight_route_module
from src.backend.delivery.api.v1.highlight_route import highlight_bp


def test_create_highlight_route_forwards_payload(flask_app_factory, monkeypatch):
    """Проверяем, что POST /highlights/ передает данные создания в use case."""
    captured = {}
    create_use_case = SimpleNamespace(execute=lambda **kwargs: captured.update(kwargs))
    monkeypatch.setattr(
        highlight_route_module,
        "container",
        SimpleNamespace(create_highlight_use_case=lambda: create_use_case),
    )
    app = flask_app_factory(highlight_bp)

    response = app.test_client().post(
        "/highlights/",
        json={
            "user_id": 1,
            "anime_id": 18,
            "episode": 1,
            "start_timestamp": "00:10",
            "end_timestamp": "00:20",
            "description": "epic",
            "emotion": "hype",
            "is_spoiler": "1",
        },
    )

    assert response.status_code == 201
    assert captured["start_timestamp"] == 10.0
    assert captured["end_timestamp"] == 20.0
    assert captured["is_spoiler"] is True


@pytest.mark.parametrize(
    ("path", "kwargs"),
    [
        ("/highlights/3?emotion=hype&query=test", {"user_id": 3}),
        ("/highlights/top?limit=5&include_spoilers=1", {"limit": 5}),
    ],
)
def test_highlight_pages_render_with_dashboard(path, kwargs, flask_app_factory, monkeypatch):
    """Проверяем, что страницы хайлайтов рендерятся при валидном dashboard-ответе use case."""
    dashboard = SimpleNamespace(
        items=[],
        anime_groups=[],
        emotions=[],
        stats=SimpleNamespace(
            total_highlights=0,
            top_anime_title="None",
            average_duration_seconds=0.0,
        ),
        selected_anime_id=None,
        selected_emotion=None,
        selected_date=None,
        selected_query=None,
        include_spoilers=True,
    )
    container = SimpleNamespace(
        get_user_highlights_use_case=lambda: SimpleNamespace(execute=lambda **payload: dashboard),
        get_public_top_highlights_use_case=lambda: SimpleNamespace(execute=lambda **payload: dashboard),
    )
    monkeypatch.setattr(highlight_route_module, "container", container)
    app = flask_app_factory(highlight_bp)

    response = app.test_client().get(path)

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("method", "path", "payload", "expected_status"),
    [
        ("put", "/highlights/5", {"description": "new", "start_timestamp": 1, "end_timestamp": 2}, 204),
        ("delete", "/highlights/5", None, 204),
    ],
)
def test_highlight_mutation_routes_delegate_to_use_cases(
    method,
    path,
    payload,
    expected_status,
    flask_app_factory,
    monkeypatch,
):
    """Проверяем, что PUT и DELETE маршруты хайлайтов делегируют работу в use case."""
    container = SimpleNamespace(
        edit_highlight_use_case=lambda: SimpleNamespace(execute=lambda **kwargs: kwargs),
        delete_highlight_use_case=lambda: SimpleNamespace(execute=lambda **kwargs: kwargs),
    )
    monkeypatch.setattr(highlight_route_module, "container", container)
    app = flask_app_factory(highlight_bp)

    response = getattr(app.test_client(), method)(path, json=payload)

    assert response.status_code == expected_status
