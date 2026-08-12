from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto import RemoveCollectionItemCommand
from backend.application.use_cases.collection.remove_collection_item import (
    RemoveCollectionItemUseCase,
)


@pytest.mark.unit
class TestRemoveCollectionItemUseCase:
    """Юнит-тесты удаления аниме из коллекции."""

    async def test_delegates_to_repository(self):
        """Что тестируем: передачу collection_id/anime_id в репозиторий.
        Что передаём: RemoveCollectionItemCommand.
        Что ожидаем: remove_item вызвана с ожидаемыми аргументами.
        """
        repo = AsyncMock()
        use_case = RemoveCollectionItemUseCase(repo)

        await use_case.execute(RemoveCollectionItemCommand(collection_id=3, anime_id=7))

        repo.remove_item.assert_awaited_once_with(collection_id=3, anime_id=7)