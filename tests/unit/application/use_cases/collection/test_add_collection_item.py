from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import AddCollectionItemCommand
from backend.application.use_cases.collection.add_collection_item import AddCollectionItemUseCase


@pytest.mark.unit
class TestAddCollectionItemUseCase:
    """Юнит-тесты добавления аниме в коллекцию."""

    async def test_builds_snapshot_and_saves_it(self):
        """Что тестируем: сборку snapshot и сохранение элемента.
        Что передаём: AddCollectionItemCommand с данными аниме.
        Что ожидаем: add_item вызвана, возвращается сохраненный элемент.
        """
        repo = AsyncMock()
        repo.add_item.side_effect = lambda item: item
        use_case = AddCollectionItemUseCase(repo)

        result = await use_case.execute(
            AddCollectionItemCommand(
                collection_id=3,
                anime_id=7,
                title="Gintama",
                description="Comedy",
                cover_url="https://example.com/cover.jpg",
                genres=["Comedy", "Action"],
            )
        )

        assert result.collection_id == 3
        assert result.anime_id == 7
        assert result.genres == ["Comedy", "Action"]