from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.collection.get_user_collections import GetUserCollectionsUseCase
from backend.domain.collection.entity import AnimeCollection, AnimeCollectionItem


@pytest.mark.unit
class TestGetUserCollectionsUseCase:
    """Юнит-тесты сбора коллекций пользователя для личной страницы."""

    async def test_maps_entities_to_view_models(self):
        """Что тестируем: сборку карточек коллекций и элементов с watch_url.
        Что передаём: одну коллекцию и один элемент.
        Что ожидаем: title и watch_url собраны корректно.
        """
        repo = AsyncMock()
        repo.get_user_collections.return_value = [
            AnimeCollection(
                id=1,
                user_id=4,
                title="Лучшие боевики",
                description="Подборка экшена",
                created_at=datetime(2026, 3, 28),
            )
        ]
        repo.get_items_count_map.return_value = {1: 1}
        repo.get_items.return_value = [
            AnimeCollectionItem(
                collection_id=1,
                anime_id=7,
                title="Gintama",
                genres=["Comedy"],
            )
        ]
        use_case = GetUserCollectionsUseCase(repo)

        result = await use_case.execute(4)

        assert result[0].collection.title == "Лучшие боевики"
        assert result[0].collection.items_count == 1
        assert result[0].items[0].watch_url == "/watch/7?episode=1"