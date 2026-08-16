from __future__ import annotations

import pytest

from backend.domain import User
from backend.domain.collection.entity import AnimeCollection, AnimeCollectionItem
from backend.infrastructure.repositories.collection_repository import CollectionRepository
from backend.infrastructure.repositories.user_repository import UserRepository


@pytest.mark.integration
class TestCollectionRepository:
    """Интеграционные тесты CollectionRepository на in-memory базе."""

    async def test_creates_collection_and_items(self, async_db_session):
        """Проверяем, что CollectionRepository создает коллекцию, добавляет элементы и читает их обратно."""
        user = await UserRepository(async_db_session).add(
            User(email="collection@example.com", username="collector", password_hash="hash")
        )
        repo = CollectionRepository(async_db_session)

        collection = await repo.create_collection(
            AnimeCollection(
                user_id=user.id,
                title="Лучшие боевики",
                description="Подборка экшена",
            )
        )
        item = await repo.add_item(
            AnimeCollectionItem(
                collection_id=collection.id,
                anime_id=7,
                title="Gintama",
                description="Comedy action",
                genres=["Comedy", "Action"],
            )
        )
        duplicate = await repo.add_item(
            AnimeCollectionItem(
                collection_id=collection.id,
                anime_id=7,
                title="Gintama",
                description="Comedy action",
                genres=["Comedy", "Action"],
            )
        )

        loaded_collection = await repo.get_by_id(collection.id)
        loaded_items = await repo.get_items(collection.id)

        assert collection.id is not None
        assert item.id == duplicate.id
        assert loaded_collection is not None
        assert loaded_collection.title == "Лучшие боевики"
        assert loaded_items[0].genres == ["Comedy", "Action"]

    async def test_returns_user_collections_and_supports_remove(self, async_db_session):
        """Проверяем, что CollectionRepository отдает коллекции пользователя и удаляет элемент по anime_id."""
        user = await UserRepository(async_db_session).add(
            User(email="collection-2@example.com", username="collector-2", password_hash="hash")
        )
        repo = CollectionRepository(async_db_session)
        collection = await repo.create_collection(
            AnimeCollection(user_id=user.id, title="Тёмные тайтлы")
        )
        await repo.add_item(
            AnimeCollectionItem(
                collection_id=collection.id,
                anime_id=8,
                title="Monster",
            )
        )

        collections = await repo.get_user_collections(user.id)
        await repo.remove_item(collection.id, 8)

        assert collections[0].title == "Тёмные тайтлы"
        assert await repo.get_items(collection.id) == []

    async def test_returns_only_public_user_collections(self, async_db_session):
        """Проверяем, что CollectionRepository отдает в публичной выборке только коллекции с is_public=True."""
        user = await UserRepository(async_db_session).add(
            User(
                email="public-collection@example.com",
                username="public-collector",
                password_hash="hash",
            )
        )
        repo = CollectionRepository(async_db_session)
        await repo.create_collection(
            AnimeCollection(user_id=user.id, title="Публичная коллекция", is_public=True)
        )
        await repo.create_collection(
            AnimeCollection(user_id=user.id, title="Приватная коллекция", is_public=False)
        )

        collections = await repo.get_public_user_collections(user.id)

        assert [item.title for item in collections] == ["Публичная коллекция"]
