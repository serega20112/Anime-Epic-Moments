from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.backend.delivery.api.v1 import watch_route as watch_route_module
from src.backend.delivery.api.v1.watch_route import watch_bp


def test_watch_page_renders_with_watch_data(flask_app_factory, monkeypatch, user_factory):
    """Проверяем, что GET /watch/<id> рендерит страницу при валидных данных плеера."""
    watch_data = SimpleNamespace(
        anime_id=1,
        anime_title="Title",
        anime_cover=None,
        anime_description="desc",
        anime_year=2024,
        anime_rating=8.0,
        genres=[],
        episode=1,
        selected_source_id=None,
        selected_translation_id=None,
        sources=[],
        highlights=[],
        current_status=None,
        last_position_seconds=0.0,
        saved_volume=1.0,
        saved_quality_label=None,
        can_discover_sources=True,
        discovery_provider_name="Kodik",
    )
    container = SimpleNamespace(
        get_watch_page_use_case=lambda: SimpleNamespace(execute=lambda **kwargs: watch_data)
    )
    monkeypatch.setattr(watch_route_module, "container", container)
    app = flask_app_factory(watch_bp, user=user_factory())

    response = app.test_client().get("/watch/1?episode=1")

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("path", "payload", "expected_status"),
    [
        ("/watch/1/status", {"status": "watching"}, 200),
        ("/watch/1/session", {"episode": 1, "watch_source_id": 2}, 200),
        (
            "/watch/1/highlights",
            {
                "episode": 1,
                "title": "Moment",
                "start_timestamp": 1.0,
                "end_timestamp": 3.0,
                "description": "desc",
                "watch_source_id": 2,
                "translation_id": 3,
            },
            201,
        ),
    ],
)
def test_watch_authenticated_routes_require_user_and_delegate(
    path,
    payload,
    expected_status,
    flask_app_factory,
    monkeypatch,
    user_factory,
):
    """Проверяем, что authenticated watch-маршруты работают при наличии пользователя в g."""
    container = SimpleNamespace(
        upsert_user_anime_status_use_case=lambda: SimpleNamespace(
            execute=lambda **kwargs: SimpleNamespace(status="watching")
        ),
        save_viewing_session_use_case=lambda: SimpleNamespace(
            execute=lambda **kwargs: SimpleNamespace(id=12)
        ),
        create_watch_highlight_use_case=lambda: SimpleNamespace(
            execute=lambda **kwargs: SimpleNamespace(id=34)
        ),
    )
    monkeypatch.setattr(watch_route_module, "container", container)
    app = flask_app_factory(watch_bp, user=user_factory())

    response = app.test_client().post(path, json=payload)

    assert response.status_code == expected_status


def test_watch_redirect_route_points_to_watch_page(flask_app_factory, monkeypatch):
    """Проверяем, что open-роут строит корректный redirect на watch-страницу."""
    monkeypatch.setattr(watch_route_module, "container", SimpleNamespace())
    app = flask_app_factory(watch_bp)

    response = app.test_client().get("/watch/open/7?episode=3")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/watch/7?episode=3")
