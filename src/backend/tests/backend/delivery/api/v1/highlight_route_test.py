from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.backend.delivery.api.v1 import highlight_route as highlight_route_module
from src.backend.delivery.api.v1.highlight_route import highlight_bp


def test_create_highlight_route_forwards_payload(flask_app_factory, monkeypatch):
    """Проверяем, что POST /highlights/ передает данные создания, включая title и category, в use case."""
    captured = {}
    create_use_case = SimpleNamespace(execute=lambda **kwargs: captured.update(kwargs) or SimpleNamespace(id=77))
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
            "title": "Epic drift",
            "category": "бой",
            "start_timestamp": "00:10",
            "end_timestamp": "00:20",
            "description": "epic",
            "emotion": "hype",
            "is_spoiler": "1",
        },
    )

    assert response.status_code == 201
    assert captured["title"] == "Epic drift"
    assert captured["category"] == "бой"
    assert captured["start_timestamp"] == 10.0
    assert captured["end_timestamp"] == 20.0
    assert captured["is_spoiler"] is True


@pytest.mark.parametrize(
    ("path", "kwargs", "with_user"),
    [
        ("/highlights/3?emotion=hype&query=test", {"user_id": 3}, True),
        ("/highlights/top?limit=5&include_spoilers=1", {"limit": 5}, True),
        ("/highlights/feed", {}, True),
        ("/highlights/following", {}, True),
        ("/highlights/saved", {}, True),
        ("/highlights/liked", {}, True),
        ("/highlights/notifications", {}, True),
        ("/highlights/share/8", {"highlight_id": 8}, False),
    ],
)
def test_highlight_pages_render_with_valid_payloads(path, kwargs, with_user, flask_app_factory, monkeypatch, user_factory):
    """Проверяем, что страницы хайлайтов рендерятся при валидных ответах use case."""
    dashboard = SimpleNamespace(
        items=[],
        anime_groups=[],
        emotions=[],
        categories=[],
        stats=SimpleNamespace(
            total_highlights=0,
            top_anime_title="None",
            average_duration_seconds=0.0,
        ),
        selected_anime_id=None,
        selected_emotion=None,
        selected_category=None,
        selected_sort="recent",
        selected_date=None,
        selected_query=None,
        include_spoilers=True,
    )
    feed = SimpleNamespace(
        popular_items=[],
        recent_items=[],
        liked_items=[],
        from_favorites_items=[],
        anime_groups=[],
        categories=[],
        selected_anime_id=None,
        selected_category=None,
        include_spoilers=False,
        profile=None,
        recent_activity=[],
    )
    following_page = SimpleNamespace(
        dashboard=dashboard,
        followed_users=[],
        total_following=0,
    )
    container = SimpleNamespace(
        get_user_highlights_use_case=lambda: SimpleNamespace(execute=lambda **payload: dashboard),
        get_public_top_highlights_use_case=lambda: SimpleNamespace(execute=lambda **payload: dashboard),
        get_highlight_feed_use_case=lambda: SimpleNamespace(execute=lambda **payload: feed),
        get_following_highlights_use_case=lambda: SimpleNamespace(execute=lambda **payload: following_page),
        get_saved_highlights_use_case=lambda: SimpleNamespace(execute=lambda **payload: dashboard),
        get_liked_highlights_use_case=lambda: SimpleNamespace(execute=lambda **payload: dashboard),
        get_highlight_notifications_use_case=lambda: SimpleNamespace(execute=lambda **payload: []),
        get_shared_highlight_use_case=lambda: SimpleNamespace(execute=lambda **payload: dashboard),
    )
    monkeypatch.setattr(highlight_route_module, "container", container)
    app = flask_app_factory(highlight_bp, user=user_factory() if with_user else None)

    response = app.test_client().get(path)

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("method", "path", "payload", "expected_status"),
    [
        ("put", "/highlights/5", {"title": "new", "description": "new", "start_timestamp": 1, "end_timestamp": 2}, 204),
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


@pytest.mark.parametrize(
    ("path", "method", "payload", "expected_status"),
    [
        ("/highlights/5/likes", "post", None, 200),
        ("/highlights/5/save", "post", None, 200),
        ("/highlights/5/comments", "post", {"content": "great"}, 201),
        ("/highlights/5/comments", "get", None, 200),
        ("/highlights/5/likes", "get", None, 200),
    ],
)
def test_highlight_social_routes_work_for_authorized_user(
    path,
    method,
    payload,
    expected_status,
    flask_app_factory,
    monkeypatch,
    user_factory,
):
    """Проверяем, что social-маршруты хайлайтов возвращают корректный ответ при наличии пользователя."""
    container = SimpleNamespace(
        get_highlight_likers_use_case=lambda: SimpleNamespace(
            execute=lambda **kwargs: [SimpleNamespace(user_id=2, username="viewer", created_at="2026-03-28 12:00")]
        ),
        set_highlight_like_use_case=lambda: SimpleNamespace(
            execute=lambda **kwargs: SimpleNamespace(id=5, likes_count=3)
        ),
        set_saved_highlight_use_case=lambda: SimpleNamespace(execute=lambda **kwargs: True),
        add_highlight_comment_use_case=lambda: SimpleNamespace(
            execute=lambda **kwargs: SimpleNamespace(id=1, user_id=1, username="tester", content="great", created_at="2026-03-28 12:00")
        ),
        get_highlight_comments_use_case=lambda: SimpleNamespace(
            execute=lambda **kwargs: [SimpleNamespace(id=1, user_id=1, username="tester", content="great", created_at="2026-03-28 12:00")]
        ),
    )
    monkeypatch.setattr(highlight_route_module, "container", container)
    app = flask_app_factory(highlight_bp, user=user_factory())

    response = getattr(app.test_client(), method)(path, json=payload)

    assert response.status_code == expected_status


@pytest.mark.parametrize(
    ("path", "expected_sort", "view_mode"),
    [
        ("/highlights/3?sort=popular", "popular", "user"),
        ("/highlights/top?sort=recent", "recent", "public"),
        ("/highlights/liked?sort=popular", "popular", "liked"),
        ("/highlights/saved?sort=popular", "popular", "saved"),
    ],
)
def test_highlight_list_routes_forward_sort_query_to_use_case(
    path,
    expected_sort,
    view_mode,
    flask_app_factory,
    monkeypatch,
    user_factory,
):
    """Проверяем, что list-маршруты хайлайтов пробрасывают sort query в соответствующий use case."""
    captured = {}
    dashboard = SimpleNamespace(
        items=[],
        anime_groups=[],
        emotions=[],
        categories=[],
        stats=SimpleNamespace(
            total_highlights=0,
            top_anime_title="None",
            average_duration_seconds=0.0,
        ),
        selected_anime_id=None,
        selected_emotion=None,
        selected_category=None,
        selected_sort=expected_sort,
        selected_date=None,
        selected_query=None,
        include_spoilers=True,
    )

    def _capture(**payload):
        captured.update(payload)
        return dashboard

    container = SimpleNamespace(
        get_user_highlights_use_case=lambda: SimpleNamespace(execute=_capture),
        get_public_top_highlights_use_case=lambda: SimpleNamespace(execute=_capture),
        get_liked_highlights_use_case=lambda: SimpleNamespace(execute=_capture),
        get_saved_highlights_use_case=lambda: SimpleNamespace(execute=_capture),
    )
    monkeypatch.setattr(highlight_route_module, "container", container)
    user = user_factory() if view_mode != "public" else None
    app = flask_app_factory(highlight_bp, user=user)

    response = app.test_client().get(path)

    assert response.status_code == 200
    assert captured["sort_by"] == expected_sort
