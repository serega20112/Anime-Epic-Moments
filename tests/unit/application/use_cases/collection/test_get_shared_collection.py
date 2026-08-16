from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.collection.get_shared_collection import (
    GetSharedCollectionUseCase,
)
from backend.domain.collection.entity import AnimeCollection, AnimeCollectionItem


@pytest.mark.unit
class TestGetSharedCollectionUseCase:
    """Юнит-тесты получения публичной коллекции для share-страницы."""

    async def test_rejects_private_collection(self):
        """Что тестируем: отклонение приватной коллекции.
        Что передаём: приватную коллекцию.
        Что ожидаем: ValueError и get_items не вызывается.
        """
        repo = AsyncMock()
        repo.get_by_id.return_value = AnimeCollection(
            id=3,
            user_id=4,
            title="Приватная подборка",
            is_public=False,
        )
        use_case = GetSharedCollectionUseCase(repo)

        with pytest.raises(ValueError):
            await use_case.execute(3)

        repo.get_items.assert_not_awaited()

    async def test_maps_public_collection(self):
        """Что тестируем: сборку share-представления публичной коллекции.
        Что передаём: публичную коллекцию и один элемент.
        Что ожидаем: корректные title, items_count, watch_url.
        """
        repo = AsyncMock()
        repo.get_by_id.return_value = AnimeCollection(
            id=3,
            user_id=4,
            title="Публичная подборка",
            description="desc",
            is_public=True,
            created_at=datetime(2026, 3, 28),
        )
        repo.get_items.return_value = [
            AnimeCollectionItem(
                collection_id=3,
                anime_id=7,
                title="Gintama",
            )
        ]
        use_case = GetSharedCollectionUseCase(repo)

        result = await use_case.execute(3)

        assert result.collection.title == "Публичная подборка"
        assert result.collection.items_count == 1
        assert result.items[0].anime_id == 7
        assert result.items[0].watch_url == "/watch/7?episode=1"
