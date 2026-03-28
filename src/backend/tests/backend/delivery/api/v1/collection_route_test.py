from __future__ import annotations

from types import SimpleNamespace

from src.backend.delivery.api.v1 import collection_route as collection_route_module
from src.backend.delivery.api.v1.collection_route import collection_bp


def test_collections_page_renders_for_authenticated_user(flask_app_factory, monkeypatch, user_factory):
    """Проверяем, что страница коллекций рендерится для авторизованного пользователя."""
    monkeypatch.setattr(
        collection_route_module,
        "container",
        SimpleNamespace(
            get_user_collections_use_case=lambda: SimpleNamespace(execute=lambda user_id: []),
            get_favorites_use_case=lambda: SimpleNamespace(execute=lambda user_id: []),
        ),
    )
    app = flask_app_factory(collection_bp, user=user_factory())

    response = app.test_client().get("/collections")

    assert response.status_code == 200


def test_collection_routes_redirect_after_write_actions(flask_app_factory, monkeypatch, user_factory):
    """Проверяем, что create/add/remove endpoints коллекций возвращают редирект на страницу коллекций."""
    monkeypatch.setattr(
        collection_route_module,
        "container",
        SimpleNamespace(
            create_collection_use_case=lambda: SimpleNamespace(execute=lambda **kwargs: None),
            add_collection_item_use_case=lambda: SimpleNamespace(execute=lambda **kwargs: None),
            remove_collection_item_use_case=lambda: SimpleNamespace(execute=lambda **kwargs: None),
        ),
    )
    app = flask_app_factory(collection_bp, user=user_factory())
    client = app.test_client()

    create_response = client.post("/collections", data={"title": "Лучшие боевики", "is_public": "1"})
    add_response = client.post(
        "/collections/1/items",
        data={"anime_id": "7", "title": "Gintama", "description": "Comedy", "genres": "Comedy"},
    )
    remove_response = client.post("/collections/1/items/remove", data={"anime_id": "7"})

    assert create_response.status_code == 302
    assert add_response.status_code == 302
    assert remove_response.status_code == 302


def test_shared_collection_page_renders_details(flask_app_factory, monkeypatch):
    """Проверяем, что share-страница коллекции рендерится по готовому CollectionDetails payload."""
    monkeypatch.setattr(
        collection_route_module,
        "container",
        SimpleNamespace(
            get_shared_collection_use_case=lambda: SimpleNamespace(
                execute=lambda collection_id: SimpleNamespace(
                    collection=SimpleNamespace(
                        id=collection_id,
                        title="Лучшие боевики",
                        description="desc",
                        items_count=1,
                        created_at="2026-03-28",
                    ),
                    items=[SimpleNamespace(title="Gintama", anime_id=7, description="", genres=[], watch_url="/watch/7?episode=1")],
                )
            )
        ),
    )
    app = flask_app_factory(collection_bp)

    response = app.test_client().get("/collections/share/1")

    assert response.status_code == 200
