from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy.exc import SQLAlchemyError

from backend.presentation.api.v1 import watch_route as watch_route_module
from backend.presentation.api.v1.watch_route import watch_bp

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
        episode_total=12,
        episode_options=[1, 2, 3],
        selected_source_id=None,
        selected_translation_id=None,
        sources=[],
        highlights=[],
        current_status=None,
        last_position_seconds=0.0,
        preferred_start_seconds=0.0,
        saved_volume=1.0,
        saved_quality_label=None,
        can_discover_sources=True,
        discovery_provider_name="Kodik",
    )
    container = SimpleNamespace(
        get_watch_page_use_case=lambda: SimpleNamespace(execute=lambda **kwargs: watch_data),
        get_anime_discussion_use_case=lambda: SimpleNamespace(
            execute=lambda **kwargs: SimpleNamespace(items=[], selected_sort="popular", total_comments=0)
        ),
    )
    monkeypatch.setattr(watch_route_module, "container", container)
    app = flask_app_factory(watch_bp, user=user_factory())

    response = app.test_client().get("/watch/1?episode=1")

    assert response.status_code == 200

def test_watch_page_renders_even_if_discussion_unavailable(
    flask_app_factory,
    monkeypatch,
):
    """Проверяем, что страница просмотра не падает, если discussion-слой временно недоступен."""
    watch_data = SimpleNamespace(
        anime_id=1,
        anime_title="Title",
        anime_cover=None,
        anime_description="desc",
        anime_year=2024,
        anime_rating=8.0,
        genres=[],
        episode=1,
        episode_total=12,
        episode_options=[1, 2, 3],
        selected_source_id=None,
        selected_translation_id=None,
        sources=[],
        highlights=[],
        current_status=None,
        last_position_seconds=0.0,
        preferred_start_seconds=0.0,
        saved_volume=1.0,
        saved_quality_label=None,
        can_discover_sources=True,
        discovery_provider_name="Kodik",
    )
    container = SimpleNamespace(
        get_watch_page_use_case=lambda: SimpleNamespace(execute=lambda **kwargs: watch_data),
        get_anime_discussion_use_case=lambda: SimpleNamespace(
            execute=lambda **kwargs: (_ for _ in ()).throw(SQLAlchemyError("db down"))
        ),
    )
    monkeypatch.setattr(watch_route_module, "container", container)
    app = flask_app_factory(watch_bp)

    response = app.test_client().get("/watch/1?episode=1")

    assert response.status_code == 200

def test_watch_page_passes_highlight_start_override_to_use_case(flask_app_factory, monkeypatch):
    """Проверяем, что GET /watch/<id> передает start_at в use case как приоритетный старт серии."""
    captured = {}
    watch_data = SimpleNamespace(
        anime_id=1,
        anime_title="Title",
        anime_cover=None,
        anime_description="desc",
        anime_year=2024,
        anime_rating=8.0,
        genres=[],
        episode=1,
        episode_total=12,
        episode_options=[1, 2, 3],
        selected_source_id=None,
        selected_translation_id=None,
        sources=[],
        highlights=[],
        current_status=None,
        last_position_seconds=30.0,
        preferred_start_seconds=15.0,
        saved_volume=1.0,
        saved_quality_label=None,
        can_discover_sources=True,
        discovery_provider_name="Kodik",
    )

    def execute(**kwargs):
        captured.update(kwargs)
        return watch_data

    container = SimpleNamespace(
        get_watch_page_use_case=lambda: SimpleNamespace(execute=execute),
        get_anime_discussion_use_case=lambda: SimpleNamespace(
            execute=lambda **kwargs: SimpleNamespace(items=[], selected_sort="popular", total_comments=0)
        ),
    )
    monkeypatch.setattr(watch_route_module, "container", container)
    app = flask_app_factory(watch_bp)

    response = app.test_client().get("/watch/1?episode=1&start_at=15")

    assert response.status_code == 200
    assert captured["preferred_start_seconds"] == 15.0

def test_watch_proxy_rewrites_hls_manifest(flask_app_factory, monkeypatch):
    """Проверяем, что media-proxy переписывает HLS-манифест на same-origin ссылки."""
    class FakeResponse:
        def __init__(self):
            self.headers = {"Content-Type": "application/x-mpegURL"}
            self.text = (
                "#EXTM3U\n"
                "#EXT-X-KEY:METHOD=AES-128,URI=\"/keys/key.bin\"\n"
                "segment-00001.ts\n"
            )

        def raise_for_status(self):
            return None

        def close(self):
            return None

    class FakeSession:
        def get(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(watch_route_module, "_proxy_media_session", FakeSession())
    app = flask_app_factory(watch_bp)

    response = app.test_client().get(
        "/watch/proxy?url=https://cache-rfn.libria.fun/videos/media/test.m3u8"
    )
    payload = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "/watch/proxy?url=" in payload
    assert "\nsegment-00001.ts\n" not in f"\n{payload}\n"

def test_watch_proxy_rejects_unknown_host(flask_app_factory, monkeypatch):
    """Проверяем, что media-proxy не проксирует произвольные внешние хосты."""
    monkeypatch.setattr(watch_route_module, "container", SimpleNamespace())
    app = flask_app_factory(watch_bp)

    response = app.test_client().get("/watch/proxy?url=https://evil.example.com/file.m3u8")

    assert response.status_code == 403

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
        (
            "/watch/1/discussion",
            {"episode": 1, "discussion_sort": "popular", "content": "Топовый тайтл"},
            302,
        ),
        (
            "/watch/discussion/comments/4/likes",
            {},
            200,
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
        add_anime_comment_use_case=lambda: SimpleNamespace(
            execute=lambda **kwargs: SimpleNamespace(id=41, likes_count=0, is_liked=False)
        ),
        set_anime_comment_like_use_case=lambda: SimpleNamespace(
            execute=lambda **kwargs: SimpleNamespace(id=4, likes_count=1, is_liked=True)
        ),
    )
    monkeypatch.setattr(watch_route_module, "container", container)
    app = flask_app_factory(watch_bp, user=user_factory())

    if path.endswith("/discussion") or path.endswith("/likes"):
        response = app.test_client().post(path, data=payload)
    else:
        response = app.test_client().post(path, json=payload)

    assert response.status_code == expected_status

@pytest.mark.parametrize(
    ("path", "payload", "request_kind", "expected_status"),
    [
        (
            "/watch/1/discussion",
            {"episode": 1, "discussion_sort": "popular", "content": "test"},
            "form",
            302,
        ),
        (
            "/watch/1/discussion",
            {"content": "test"},
            "json",
            503,
        ),
        (
            "/watch/discussion/comments/4/likes",
            {},
            "form",
            503,
        ),
    ],
)
def test_watch_discussion_routes_fail_gracefully_on_storage_error(
    path,
    payload,
    request_kind,
    expected_status,
    flask_app_factory,
    monkeypatch,
    user_factory,
):
    """Проверяем, что discussion-эндпоинты не отдают 500 при ошибке слоя хранения."""
    container = SimpleNamespace(
        add_anime_comment_use_case=lambda: SimpleNamespace(
            execute=lambda **kwargs: (_ for _ in ()).throw(SQLAlchemyError("db down"))
        ),
        set_anime_comment_like_use_case=lambda: SimpleNamespace(
            execute=lambda **kwargs: (_ for _ in ()).throw(SQLAlchemyError("db down"))
        ),
    )
    monkeypatch.setattr(watch_route_module, "container", container)
    app = flask_app_factory(watch_bp, user=user_factory())

    if request_kind == "json":
        response = app.test_client().post(path, json=payload)
    else:
        response = app.test_client().post(path, data=payload)

    assert response.status_code == expected_status

def test_watch_redirect_route_points_to_watch_page(flask_app_factory, monkeypatch):
    """Проверяем, что open-роут строит корректный redirect на watch-страницу."""
    monkeypatch.setattr(watch_route_module, "container", SimpleNamespace())
    app = flask_app_factory(watch_bp)

    response = app.test_client().get("/watch/open/7?episode=3")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/watch/7?episode=3")
