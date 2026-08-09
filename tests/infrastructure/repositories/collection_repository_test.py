from __future__ import annotations

from backend.infrastructure.repositories.user_repository import UserRepository

from backend.domain import User
from backend.domain.collection.entity import AnimeCollection, AnimeCollectionItem
from backend.infrastructure.repositories.collection_repository import CollectionRepository


def test_collection_repository_creates_collection_and_items(db_session):
    """Проверяем, что CollectionRepository создает коллекцию, добавляет элементы и читает их обратно."""
    user = UserRepository(db_session).add(
        User(email="collection@example.com", username="collector", password_hash="hash")
    )
    repo = CollectionRepository(db_session)

    collection = repo.create_collection(
        AnimeCollection(
            user_id=user.id,
            title="Лучшие боевики",
            description="Подборка экшена",
        )
    )
    item = repo.add_item(
        AnimeCollectionItem(
            collection_id=collection.id,
            anime_id=7,
            title="Gintama",
            description="Comedy action",
            genres=["Comedy", "Action"],
        )
    )
    duplicate = repo.add_item(
        AnimeCollectionItem(
            collection_id=collection.id,
            anime_id=7,
            title="Gintama",
            description="Comedy action",
            genres=["Comedy", "Action"],
        )
    )

    loaded_collection = repo.get_by_id(collection.id)
    loaded_items = repo.get_items(collection.id)

    assert collection.id is not None
    assert item.id == duplicate.id
    assert loaded_collection is not None
    assert loaded_collection.title == "Лучшие боевики"
    assert loaded_items[0].genres == ["Comedy", "Action"]


def test_collection_repository_returns_user_collections_and_supports_remove(db_session):
    """Проверяем, что CollectionRepository отдает коллекции пользователя и удаляет элемент по anime_id."""
    user = UserRepository(db_session).add(
        User(email="collection-2@example.com", username="collector-2", password_hash="hash")
    )
    repo = CollectionRepository(db_session)
    collection = repo.create_collection(
        AnimeCollection(user_id=user.id, title="Тёмные тайтлы")
    )
    repo.add_item(
        AnimeCollectionItem(
            collection_id=collection.id,
            anime_id=8,
            title="Monster",
        )
    )

    collections = repo.get_user_collections(user.id)
    repo.remove_item(collection.id, 8)

    assert collections[0].title == "Тёмные тайтлы"
    assert repo.get_items(collection.id) == []


def test_collection_repository_returns_only_public_user_collections(db_session):
    """Проверяем, что CollectionRepository отдает в публичной выборке только коллекции с is_public=True."""
    user = UserRepository(db_session).add(
        User(email="public-collection@example.com", username="public-collector", password_hash="hash")
    )
    repo = CollectionRepository(db_session)
    repo.create_collection(
        AnimeCollection(user_id=user.id, title="Публичная коллекция", is_public=True)
    )
    repo.create_collection(
        AnimeCollection(user_id=user.id, title="Приватная коллекция", is_public=False)
    )

    collections = repo.get_public_user_collections(user.id)

    assert [item.title for item in collections] == ["Публичная коллекция"]
