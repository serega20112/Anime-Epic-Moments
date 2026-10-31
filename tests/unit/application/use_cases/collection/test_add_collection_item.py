from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.dto import AddCollectionItemCommand
from backend.application.use_cases.collection.add_collection_item import (
    AddCollectionItemUseCase,
    CollectionAccessError,
)
from backend.domain.aggregates.collection.collection import AnimeCollection
from tests.support.fakes import FakeUnitOfWork


@pytest.mark.unit
class TestAddCollectionItemUseCase:
    """Юнит-тесты добавления аниме в коллекцию."""

    async def test_builds_snapshot_and_saves_it(self):
        """Что тестируем: сборку snapshot и сохранение элемента.
        Что передаём: команду с заполненным названием и коллекцию владельца.
        Что ожидаем: add_item вызвана, возвращается сохраненный элемент.
        """
        repo = AsyncMock()
        repo.get_by_id.return_value = AnimeCollection(id=3, user_id=1, title="Моя")
        repo.add_item.side_effect = lambda item: item
        use_case = AddCollectionItemUseCase(
            FakeUnitOfWork(CollectionRepository=repo),
            AsyncMock(),
        )

        result = await use_case.execute(
            AddCollectionItemCommand(
                collection_id=3,
                anime_id=7,
                user_id=1,
                title="Gintama",
                description="Comedy",
                cover_url="https://example.com/cover.jpg",
                genres=["Comedy", "Action"],
            )
        )

        assert result.collection_id == 3
        assert result.anime_id == 7
        assert result.genres == ["Comedy", "Action"]

    async def test_fills_snapshot_from_catalog(self):
        """Что тестируем: обогащение снимка через клиент каталога.
        Что передаём: команду без названия и аниме с названием из API.
        Что ожидаем: элемент сохранён с названием из каталога.
        """
        repo = AsyncMock()
        repo.get_by_id.return_value = AnimeCollection(id=3, user_id=1, title="Моя")
        repo.add_item.side_effect = lambda item: item
        anime_client = AsyncMock()
        anime_client.get_by_id.return_value = SimpleNamespace(
            title="Gintama",
            description="Comedy",
            cover_url=None,
            genres=[],
            original_title=None,
        )
        use_case = AddCollectionItemUseCase(FakeUnitOfWork(CollectionRepository=repo), anime_client)

        result = await use_case.execute(
            AddCollectionItemCommand(collection_id=3, anime_id=7, user_id=1)
        )

        assert result.title == "Gintama"
        anime_client.get_by_id.assert_awaited_once_with(7)

    async def test_rejects_foreign_collection(self):
        """Что тестируем: запрет добавления в чужую коллекцию.
        Что передаём: команду пользователя 1 для коллекции пользователя 99.
        Что ожидаем: CollectionAccessError, add_item не вызывается.
        """
        repo = AsyncMock()
        repo.get_by_id.return_value = AnimeCollection(id=3, user_id=99, title="Чужая")
        use_case = AddCollectionItemUseCase(FakeUnitOfWork(CollectionRepository=repo), AsyncMock())

        with pytest.raises(CollectionAccessError):
            await use_case.execute(
                AddCollectionItemCommand(
                    collection_id=3,
                    anime_id=7,
                    user_id=1,
                    title="Gintama",
                )
            )

        repo.add_item.assert_not_awaited()
